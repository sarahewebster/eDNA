#!/usr/bin/env python3
"""
Test the eDNA pumping system.
"""
import sys
import argparse
import time
import os.path
import logging
from typing import Tuple, Any, Dict
from collections import OrderedDict, namedtuple
try:
    import RPi.GPIO as GPIO # type: ignore
except ImportError:
    import edna.mockgpio as GPIO # type: ignore
try:
    from Adafruit_ADS1x15 import ADS1115 # type: ignore
except ImportError:
    from edna.mockpr import Adc as ADS1115
from edna import ticker
from edna.periph import Valve, FlowMeter, Pump, read_pressure
from edna.config import Config, BadEntry


PrSensor = namedtuple("PrSensor", ["chan", "gain", "prmax"])


class DataWriter(object):
    def __init__(self, outf: Any):
        self.outf = outf

    def writerec(self, rec: OrderedDict):
        for k, v in rec.items():
            print("{}={} ".format(k, v), end="", file=self.outf)
        print("", file= self.outf)


def parse_cmdline() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test the eDNA pumping system")
    parser.set_defaults(syscfg=os.environ.get("EDNA_SYSCFG", os.path.expanduser("~/.config/edna/system.cfg")))
    parser.add_argument("pump", metavar="NAME",
                        help="pump to run; sample or ethanol")
    parser.add_argument("--syscfg", metavar="FILE",
                        help="location of the system confguration file (default: %(default)s)")
    parser.add_argument("--valve",
                        type=str,
                        default="1",
                        help="valve to open; 1, 2, 3 or ethanol (default: %(default)s)")
    parser.add_argument("--rate", metavar="HZ",
                        type=float,
                        default=2,
                        help="flow meter sampling rate in Hz (default: %(default)s)")
    parser.add_argument("--clean", action="store_true",
                        help="restore boot-up GPIO settings on exit")
    return parser.parse_args()


def runtest(cfg: Config, args: argparse.Namespace, wtr: DataWriter) -> bool:
    logger = logging.getLogger()
    # Extract parameters from configuration files
    try:
        sens = dict()
        adc = ADS1115(address=cfg.get_int('Adc', 'Addr'),
                      busnum=cfg.get_int('Adc', 'Bus'))
        sens["Filter"] = PrSensor(chan=cfg.get_int('Pressure.Filter', 'Chan'),
                                gain=cfg.get_expr('Pressure.Filter', 'Gain'),
                                prmax=cfg.get_float('Pressure.Filter', 'Max'))

        def checkpr() -> Tuple[float, bool]:
            psi = read_pressure(adc, sens["Filter"].chan, gain=sens["Filter"].gain)
            return psi, psi < sens["Filter"].prmax

        pumps = dict()
        for key in ("Sample", "Ethanol"):
            pumps[key.lower()] = Pump(cfg.get_int('Motor.'+key, 'Enable'))

        valves = dict()
        for key in ("1", "2", "3", "Ethanol"):
            vkey = "Valve." + key
            valves[key.lower()] = Valve(cfg.get_int(vkey, 'Enable'),
                                cfg.get_int(vkey, 'Power'),
                                cfg.get_int(vkey, 'Gnd'))

        fm = FlowMeter(cfg.get_int('FlowSensor', 'Input'),
                       cfg.get_int('FlowSensor', 'Ppl'))
    except BadEntry as e:
        logger.exception("Configuration error")
        return False

    if args.pump not in pumps:
        logger.critical("Invalid pump name: '%s'", args.pump)
        return False

    if args.valve not in valves:
        logger.critical("Invalid valve: '%s'", args.valve)
        return False

    t0 = time.time()
    interval = 1./args.rate
    print("Enter ctrl-c to exit ...", file=sys.stderr)
    try:
        fm.reset()
        with valves[args.valve]:
            with pumps[args.pump]:
                for tick in ticker(interval):
                    amount, secs = fm.amount()
                    pr, pr_ok = checkpr()
                    wtr.writerec(OrderedDict(elapsed=round(secs, 3),
                                             vol=round(amount, 3),
                                             pr=round(pr, 3)))
    except KeyboardInterrupt:
        print("done", file=sys.stderr)

    return True


def main() -> int:
    args = parse_cmdline()

    try:
        cfg = Config(args.syscfg)
    except Exception as e:
        print("Error loading system config file; " + str(e), file=sys.stderr)
        return 1

    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.INFO,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        stream=sys.stderr)
    # eDNA uses the Broadcom SOC pin numbering scheme
    GPIO.setmode(GPIO.BCM)
    status = False
    try:
        status = runtest(cfg, args, DataWriter(sys.stdout))
    except Exception as e:
        logging.exception("Error running the pump test")
    finally:
        if args.clean:
            GPIO.cleanup()
    return 0 if status else 1


if __name__ == "__main__":
    sys.exit(main())
