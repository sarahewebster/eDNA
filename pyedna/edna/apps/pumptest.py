#!/usr/bin/env python3
"""
Test the eDNA pumping system.
"""
import sys
import argparse
import time
import os.path
import logging
from typing import Tuple, Optional
from collections import OrderedDict
try:
    import RPi.GPIO as GPIO # type: ignore
except ImportError:
    import edna.mockgpio as GPIO # type: ignore
try:
    from Adafruit_ADS1x15 import ADS1115 # type: ignore
except ImportError:
    from edna.mockpr import Adc as ADS1115
from edna import ticker
from edna.periph import Valve, AnalogFlowMeter, Pump, PrSensor
from edna.config import Config, BadEntry
from edna.sample import Datafile


def writerec(rec: OrderedDict):
    for k, v in rec.items():
        print("{}={} ".format(k, v), end="")
    print("")


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
        sens["Filter"] = PrSensor(adc,
                                  cfg.get_int('Pressure.Filter', 'Chan'),
                                  cfg.get_expr('Pressure.Filter', 'Gain'))

        prmax = cfg.get_float('Pressure.Filter', 'Max')
        def checkpr() -> Tuple[float, bool]:
            psi = sens["Filter"].read()
            return psi, psi < prmax

        pumps = dict()
        for key in ("Sample", "Ethanol"):
            pumps[key.lower()] = Pump(cfg.get_int('Motor.'+key, 'Enable'))

        valves = dict()
        for key in ("1", "2", "3", "Ethanol"):
            vkey = "Valve." + key
            valves[key.lower()] = Valve(cfg.get_int(vkey, 'Enable'),
                                        cfg.get_int(vkey, 'IN1'),
                                        cfg.get_int(vkey, 'IN2'),
                                        lopen=cfg.get_string(vkey, 'open'),
                                        lclose=cfg.get_string(vkey, 'close'))


        fm = AnalogFlowMeter(adc,
                             cfg.get_int('AnalogFlowSensor', 'Chan'),
                             cfg.get_expr('AnalogFlowSensor', 'Gain'),
                             cfg.get_array('AnalogFlowSensor', 'Coeff'))
    except BadEntry:
        logger.exception("Configuration error")
        return False

    if args.pump not in pumps:
        logger.critical("Invalid pump name: '%s'", args.pump)
        return False

    if args.valve not in valves:
        logger.critical("Invalid valve: '%s'", args.valve)
        return False

    interval = 1./args.rate
    print("Enter ctrl-c to exit ...", file=sys.stderr)
    try:
        fm.reset()
        with valves[args.valve]:
            with pumps[args.pump]:
                for tick in ticker(interval):
                    amount, secs = fm.amount()
                    pr, pr_ok = checkpr()
                    rec = OrderedDict(elapsed=round(secs, 3),
                                      vol=round(amount, 3),
                                      pr=round(pr, 3))
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
    # eDNA uses the Broadcom SOC pin numbering scheme
    GPIO.setmode(GPIO.BCM)
    # If we don't suppress warnings, as message will be printed to stderr
    # everytime GPIO.setup is called on a pin that isn't in the default
    # state (input).
    GPIO.setwarnings(False)

    status = False
    try:
        if args.out:
            status = runtest(cfg, args, Datafile(args.out))
        else:
            status = runtest(cfg, args, None)
    except Exception as e:
        logging.exception("Error running the pump test")
    finally:
        if args.clean:
            GPIO.cleanup()
    return 0 if status else 1


if __name__ == "__main__":
    sys.exit(main())
