#!/usr/bin/env python3
#
# Run an eDNA deployment
#
import sys
import os
import os.path
import argparse
import time
import logging
import datetime
import tarfile
from typing import Callable, Tuple, NamedTuple
from functools import partial
from collections import OrderedDict
try:
    import RPi.GPIO as GPIO # type: ignore
except ImportError:
    import edna.mockgpio as GPIO # type: ignore
    GPIO.detector_freq = 20
try:
    from Adafruit_ADS1x15 import ADS1115 # type: ignore
except ImportError:
    from edna.mockpr import Adc as ADS1115
from edna import ticker
from edna.sample import Datafile, FlowLimits, collect, seekdepth
from edna.periph import Valve, Pump, FlowMeter, LED, \
    read_pressure, psia_to_dbar, blinker, fader
from edna.config import Config, BadEntry


class PrSensor(NamedTuple):
    chan: int
    gain: float
    prmax: float = 0


class LedCtl(NamedTuple):
    obj: LED
    fast: float
    slow: float
    fade: float


class Deployment(object):
    id: str
    dir: str
    seek_err: float
    seek_time: float
    depth_err: float
    pr_rate: float

    def __init__(self, id: str, dir: str,
                 seek_err: float = 0, seek_time: float = 0,
                 depth_err: float = 0, pr_rate: float = 0):
        self.id, self.dir = id, dir
        self.seek_err = seek_err
        self.seek_time = seek_time
        self.depth_err = depth_err
        self.pr_rate = pr_rate


def parse_cmdline() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run an eDNA deployment")
    parser.set_defaults(syscfg=os.environ.get("EDNA_SYSCFG", os.path.expanduser("~/.config/edna/system.cfg")),
                        datadir=os.environ.get("EDNA_DATADIR", os.path.expanduser("~/data")),
                        outbox=os.environ.get("EDNA_OUTBOX", os.path.expanduser("~/OUTBOX")))
    parser.add_argument("cfg", metavar="FILE",
                        help="deployment configuration file")
    parser.add_argument("--syscfg", metavar="FILE",
                        help="system confguration file (default: %(default)s)")
    parser.add_argument("--datadir", metavar="DIR",
                        help="data directory (default: %(default)s)")
    parser.add_argument("--clean", action="store_true",
                        help="restore boot-up GPIO settings on exit")
    return parser.parse_args()


def init_logging(datadir: str, id: str):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    # Important messages to standard error
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # Everything to the deployment log file
    fh = logging.FileHandler(os.path.join(datadir, ("_".join(["edna", id]))+".log"))
    fh.setLevel(logging.DEBUG)

    fmtr = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fmtr.default_msec_format = "%s.%03d"
    ch.setFormatter(fmtr)
    fh.setFormatter(fmtr)
    logger.addHandler(fh)
    logger.addHandler(ch)


def runedna(cfg: Config, deployment: Deployment, df: Datafile) -> bool:
    logger = logging.getLogger()
    logger.info("Starting deployment: %s", deployment.id)

    # Extract parameters from configuration files
    try:
        pr = dict()
        adc = ADS1115(address=cfg.get_int('Adc', 'Addr'),
                      busnum=cfg.get_int('Adc', 'Bus'))
        pr["Filter"] = PrSensor(chan=cfg.get_int('Pressure.Filter', 'Chan'),
                                gain=cfg.get_expr('Pressure.Filter', 'Gain'),
                                prmax=cfg.get_float('Pressure.Filter', 'Max'))
        pr["Env"] = PrSensor(chan=cfg.get_int('Pressure.Env', 'Chan'),
                             gain=cfg.get_expr('Pressure.Env', 'Gain'),
                             prmax=0)

        def checkpr() -> Tuple[float, bool]:
            psi = read_pressure(adc, pr["Filter"].chan, gain=pr["Filter"].gain)
            return psi, psi < pr["Filter"].prmax

        def checkdepth(limits: Tuple[float, float]) -> Tuple[float, bool]:
            dbar = psia_to_dbar(read_pressure(adc, pr["Env"].chan, gain=pr["Env"].gain))
            return dbar, limits[0] <= dbar <= limits[1]

        pumps = dict()
        for key in ("Sample", "Ethanol"):
            pumps[key] = Pump(cfg.get_int('Motor.'+key, 'Enable'))

        valves = dict()
        for key in ("1", "2", "3", "Ethanol"):
            vkey = "Valve." + key
            valves[key] = Valve(cfg.get_int(vkey, 'Enable'),
                                cfg.get_int(vkey, 'Power'),
                                cfg.get_int(vkey, 'Gnd'))

        fm = FlowMeter(cfg.get_int('FlowSensor', 'Input'),
                       cfg.get_int('FlowSensor', 'Ppl'))
        sample_rate = cfg.get_float('FlowSensor', 'Rate')
        ledctl = LedCtl(obj=LED(cfg.get_int("LED", "GPIO")),
                        fast=cfg.get_float("LED", "fast"),
                        slow=cfg.get_float("LED", "slow"),
                        fade=cfg.get_float("LED", "fade"))

        limits = dict()
        for key in ("Sample", "Ethanol"):
            limits[key] = FlowLimits(amount=cfg.get_float('Collect.'+key, 'Amount'),
                                     time=cfg.get_float('Collect.'+key, 'Time'))

        deployment.seek_err = cfg.get_float('Deployment', 'SeekErr')
        deployment.depth_err = cfg.get_float('Deployment', 'DepthErr')
        deployment.pr_rate = cfg.get_float('Deployment', 'PrRate')
        deployment.seek_time = cfg.get_int('Deployment', 'SeekTime')

        # Each entry in depths is a tuple containing the depth and
        # the sample index.
        depths = []
        for i, key in enumerate(['Sample.1', 'Sample.2', 'Sample.3']):
            depths.append((cfg.get_float(key, 'Depth'), i+1))
    except BadEntry as e:
        logger.exception("Configuration error")
        return False

    # Samples are collected in depth order, not index order.
    depths.sort(key=lambda e: e[0])
    for target, index in depths:
        logger.info("Seeking depth for sample %d; %.2f +/- %.2f",
                    index, target, deployment.seek_err)
        drange = (target-deployment.seek_err, target+deployment.seek_err)
        with blinker(ledctl.obj, ledctl.slow):
            depth, status = seekdepth(df,
                                      partial(checkdepth, drange),
                                      deployment.pr_rate,
                                      deployment.seek_time)
        if not status:
            logger.critical("Depth seek time limit expired. Aborting.")
            return False

        logger.info("Collecting sample %d", index)
        drange = (depth-deployment.depth_err, depth+deployment.depth_err)
        status = collect(df, index,
                         (pumps["Sample"], pumps["Ethanol"]),
                         (valves[str(index)], valves["Ethanol"]),
                         fm, sample_rate,
                         (limits["Sample"], limits["Ethanol"]),
                         checkpr,
                         partial(checkdepth,drange))


    return True


def main() -> int:
    args = parse_cmdline()

    try:
        cfg = Config(args.syscfg)
    except Exception as e:
        print("Error loading system config file; " + str(e), file=sys.stderr)
        return 1

    try:
        cfg.load(args.cfg)
    except Exception as e:
        print("Error loading deployment config file; " + str(e), file=sys.stderr)
        return 1

    # Validate configuration files
    missing = cfg.validate()
    if missing:
        print("Missing configuration entries: {}".format(";".join(missing)))
        return 1

    # Generate deployment ID and directory name
    id = datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y%m%dT%H%M%S")
    dir = os.path.join(args.datadir, "edna_" + id)
    deployment = Deployment(id=id, dir=dir)

    # Create deployment directory
    os.makedirs(deployment.dir, exist_ok=True)
    # Initialize logging
    init_logging(deployment.dir, deployment.id)
    # Save configuration to deployment directory
    with open(os.path.join(deployment.dir, "deploy.cfg"), "w") as fp:
        cfg.write(fp)

    logger = logging.getLogger()
    # eDNA uses the Broadcom SOC pin numbering scheme
    GPIO.setmode(GPIO.BCM)

    status = False
    try:
        name = "edna_" + deployment.id + ".ndjson"
        with open(os.path.join(deployment.dir, name), "w") as fp:
            status = runedna(cfg, deployment, Datafile(fp))
    except Exception:
        logger.exception("Deployment aborted with an exception")
    else:
        os.makedirs(args.outbox, exist_ok=True)
        # Archive the deployment directory to the OUTBOX
        arpath = os.path.join(args.outbox, "edna_" + deployment.id + ".tar.gz")
        logger.info("Archiving deployment directory to %s", arpath)
        with tarfile.open(arpath, "w:gz") as tar:
            tar.add(deployment.dir)
    finally:
        if args.clean:
            GPIO.cleanup()

    return 0 if status else 1


if __name__ == "__main__":
    sys.exit(main())
