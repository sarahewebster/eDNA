#!/usr/bin/env python3
"""
Test the eDNA pressure sensors.
"""
import sys
import argparse
import time
import os.path
import logging
from typing import Tuple, Any, Dict
from collections import OrderedDict, namedtuple
try:
    from Adafruit_ADS1x15 import ADS1115 # type: ignore
except ImportError:
    from edna.mockpr import Adc as ADS1115
from edna import ticker
from edna.periph import read_pressure
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
    parser = argparse.ArgumentParser(description="Test an eDNA pressure sensor")
    parser.set_defaults(syscfg=os.environ.get("EDNA_SYSCFG", os.path.expanduser("~/.config/edna/system.cfg")))
    parser.add_argument("sensor", metavar="NAME",
                        help="pressure sensor to test; env or filter")
    parser.add_argument("--syscfg", metavar="FILE",
                        help="location of the system confguration file")
    parser.add_argument("--rate", metavar="HZ",
                        type=float,
                        default=2,
                        help="sensor sampling rate in Hz")
    return parser.parse_args()


def runtest(cfg: Config, args: argparse.Namespace, wtr: DataWriter) -> bool:
    logger = logging.getLogger()
    # Extract parameters from configuration files
    try:
        sens = dict()
        adc = ADS1115(address=cfg.get_int('Adc', 'Addr'),
                      busnum=cfg.get_int('Adc', 'Bus'))
        sens["Env"] = PrSensor(chan=cfg.get_int('Pressure.Env', 'Chan'),
                             gain=cfg.get_float('Pressure.Env', 'Gain'),
                             prmax=0)
        sens["Filter"] = PrSensor(chan=cfg.get_int('Pressure.Filter', 'Chan'),
                                gain=cfg.get_float('Pressure.Filter', 'Gain'),
                                prmax=cfg.get_float('Pressure.Filter', 'Max'))

        def checkpr() -> Tuple[float, bool]:
            psi = read_pressure(adc, sens["Filter"].chan, gain=sens["Filter"].gain)
            return psi, psi < sens["Filter"].prmax
    except BadEntry as e:
        logger.exception("Configuration error")
        return False

    t0 = time.time()
    interval = 1./args.rate
    print("Enter ctrl-c to exit ...", file=sys.stderr)
    try:
        for tick in ticker(interval):
            psi = read_pressure(adc, sens[args.sensor].chan, gain=sens[args.sensor].gain)
            wtr.writerec(OrderedDict(elapsed=round(tick, 3),
                                     pr=round(psi, 3)))
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
    try:
        status = runtest(cfg, args, DataWriter(sys.stdout))
    except Exception as e:
        logging.exception("Error running the sensor test")

    return 0 if status else 1


if __name__ == "__main__":
    sys.exit(main())
