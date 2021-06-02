#!/usr/bin/env python3
"""
Test the eDNA analog flow meter
"""
import sys
import argparse
import os.path
import logging
from typing import Optional
from collections import OrderedDict
try:
    from Adafruit_ADS1x15 import ADS1115 # type: ignore
except ImportError:
    from edna.mockpr import Adc as ADS1115
from edna import ticker
from edna.periph import AnalogFlowMeter
from edna.config import Config, BadEntry
from edna.sample import Datafile


def writerec(rec: OrderedDict):
    for k, v in rec.items():
        print("{}={} ".format(k, v), end="")
    print("")


def parse_cmdline() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read the eDNA flow meter")
    parser.set_defaults(syscfg=os.environ.get("EDNA_SYSCFG", os.path.expanduser("~/.config/edna/system.cfg")))
    parser.add_argument("--syscfg", metavar="FILE",
                        help="location of the system confguration file")
    parser.add_argument("--rate", metavar="HZ",
                        type=float,
                        default=2,
                        help="sensor sampling rate in Hz")
    parser.add_argument("--out", type=argparse.FileType("w"),
                        help="write data to output file")
    return parser.parse_args()


def runtest(cfg: Config, args: argparse.Namespace, df: Optional[Datafile]) -> bool:
    logger = logging.getLogger()
    # Extract parameters from configuration files
    try:
        adc = ADS1115(address=cfg.get_int('Adc', 'Addr'),
                      busnum=cfg.get_int('Adc', 'Bus'))
        sens = AnalogFlowMeter(adc,
                               cfg.get_int('AnalogFlowSensor', 'Chan'),
                               cfg.get_expr('AnalogFlowSensor', 'Gain'),
                               cfg.get_array('AnalogFlowSensor', 'Coeff'))
    except BadEntry:
        logger.exception("Configuration error")
        return False

    interval = 1./args.rate
    print("Enter ctrl-c to exit ...", file=sys.stderr)
    sens.reset()
    try:
        for tick in ticker(interval):
            vol, secs = sens.amount()
            rec = OrderedDict(elapsed=round(secs, 3),
                              vol=round(vol, 3))
            writerec(rec)
            if df:
                df.add_record("flow", rec, ts=tick)
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
    except Exception:
        logging.exception("Error running the sensor test")

    return 0 if status else 1


if __name__ == "__main__":
    sys.exit(main())
