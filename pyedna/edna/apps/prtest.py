#!/usr/bin/env python3
"""
Test the eDNA pressure sensors.
"""
import sys
import argparse
import time
import os.path
import logging
from typing import Tuple, Any, Dict, Optional
from collections import OrderedDict, namedtuple
try:
    from Adafruit_ADS1x15 import ADS1115 # type: ignore
except ImportError:
    from edna.mockpr import Adc as ADS1115
from edna import ticker
from edna.periph import PrSensor, psia_to_dbar
from edna.config import Config, BadEntry
from edna.sample import Datafile


def writerec(rec: OrderedDict):
    for k, v in rec.items():
        print("{}={} ".format(k, v), end="")
    print("")


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
    parser.add_argument("--dbars", action="store_true",
                        help="output gauge pressure in decibars")
    parser.add_argument("--out", type=argparse.FileType("w"),
                        help="write data to output file")
    return parser.parse_args()


def runtest(cfg: Config, args: argparse.Namespace, df: Optional[Datafile]) -> bool:
    logger = logging.getLogger()
    # Extract parameters from configuration files
    try:
        sens = dict()
        adc = ADS1115(address=cfg.get_int('Adc', 'Addr'),
                      busnum=cfg.get_int('Adc', 'Bus'))
        sens["env"] = PrSensor(adc,
                               cfg.get_int('Pressure.Env', 'Chan'),
                               cfg.get_expr('Pressure.Env', 'Gain'),
                               coeff=cfg.get_array('Pressure.Env', 'Coeff'))
        sens["filter"] = PrSensor(adc,
                                  cfg.get_int('Pressure.Filter', 'Chan'),
                                  cfg.get_expr('Pressure.Filter', 'Gain'),
                                  coeff=cfg.get_array('Pressure.Filter', 'Coeff'))

    except BadEntry as e:
        logger.exception("Configuration error")
        return False

    t0 = time.time()
    interval = 1./args.rate
    print("Enter ctrl-c to exit ...", file=sys.stderr)
    try:
        for tick in ticker(interval):
            psi = sens[args.sensor].read()
            if args.dbars:
                rec = OrderedDict(elapsed=round(tick-t0, 3),
                                  dbars=round(psia_to_dbar(psi), 3))
            else:
                rec = OrderedDict(elapsed=round(tick-t0, 3),
                                  psi=round(psi, 3))
            writerec(rec)
            if df:
                df.add_record("pr", rec, ts=tick)
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
    status = False
    try:
        if args.out:
            status = runtest(cfg, args, Datafile(args.out))
        else:
            status = runtest(cfg, args, None)
    except Exception as e:
        logging.exception("Error running the sensor test")

    return 0 if status else 1


if __name__ == "__main__":
    sys.exit(main())
