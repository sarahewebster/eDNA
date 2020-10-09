#!/usr/bin/env python3
#
# Run a priming cycle on one of the eDNA flow paths
#
import sys
import argparse
import time
import logging
from typing import Callable, Tuple
from contextlib import contextmanager
try:
    import RPi.GPIO as GPIO # type: ignore
except ImportError:
    import edna.mockgpio as GPIO
try:
    from Adafruit_ADS1x15 import ADS1115 # type: ignore
except ImportError:
    from edna.mockpr import Adc as ADS1115
from edna.periph import Valve, read_pressure
from edna.config import Config, BadEntry


@contextmanager
def gpio_high(line: int):
    GPIO.output(line, GPIO.HIGH)
    yield
    GPIO.output(line, GPIO.LOW)


def prime_cycle(vsamp: Valve, veth: Valve, motor: int,
                checkpr: Callable[[], Tuple[float, bool]],
                tlimit: float):
    t0 = time.time()
    with veth:
        with vsamp:
            with gpio_high(motor):
                while (time.time() - t0) < tlimit:
                    psi, ok = checkpr()
                    if not ok:
                        logging.warning("Max pressure exceeded: %.2f psi", psi)
                    time.sleep(0.5)


def main():
    parser = argparse.ArgumentParser(description="Prime an eDNA flow path")
    parser.add_argument("cfg", metavar="FILE",
                        help="system configuration file")
    parser.add_argument("valve", metavar="N",
                        type=int,
                        help="valve# to prime, 1-3")
    parser.add_argument("--time", metavar="SECS",
                        type=float,
                        default=30,
                        help="runtime in seconds")
    parser.add_argument("--prmax", metavar="PSI",
                        type=float,
                        default=12,
                        help="maximum filter pressure in psi")
    args = parser.parse_args()

    try:
        cfg = Config(args.cfg)
    except Exception as e:
        print("Error loading config file; " + str(e), file=sys.stderr)
        sys.exit(1)

    if args.valve < 1 or args.valve > 3:
        print("Valve number must be between 1 and 3", file=sys.stderr)
        sys.exit(1)

    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.INFO,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        stream=sys.stderr)

    # eDNA uses the Broadcom SOC pin numbering scheme
    GPIO.setmode(GPIO.BCM)
    try:
        adc = ADS1115(address=0x48, busnum=cfg.get_int('Adc', 'Bus'))
        pr_chan = cfg.get_int('Pressure.Filter', 'Chan')
        pr_gain = cfg.get_float('Pressure.Filter', 'Gain')

        motor = cfg.get_int('Motor.Sample', 'Enable')
        GPIO.setup(motor, GPIO.OUT)

        # Config file key for valve
        vkey = "Valve." + str(args.valve)
        sample_valve = Valve(cfg.get_int(vkey, 'Enable'),
                             cfg.get_int(vkey, 'Power'),
                             cfg.get_int(vkey, 'Gnd'))
        eth_valve = Valve(cfg.get_int('Valve.Ethanol', 'Enable'),
                          cfg.get_int('Valve.Ethanol', 'Power'),
                          cfg.get_int('Valve.Ethanol', 'Gnd'))
    except BadEntry as e:
        print(str(e), file=sys.stderr)
        GPIO.cleanup()
        sys.exit(2)

    def checkpr():
        psi = read_pressure(adc, pr_chan, gain=pr_gain)
        return psi, psi < args.prmax

    try:
        prime_cycle(sample_valve, eth_valve, motor, checkpr, args.time)
    finally:
        GPIO.cleanup()


if __name__ == "__main__":
    main()
