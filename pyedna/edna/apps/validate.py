#!/usr/bin/env python3
#
# Validate one or more eDNA configuration files.
#
import sys
import argparse
import os.path
from typing import List, Dict
from edna.config import Config, BadEntry



valve_req: List[str] = ["enable", "power", "gnd"]
motor_req: List[str] = ["enable", "hz"]
pressure_req: List[str] = ["chan", "gain"]
collect_req: List[str] = ["amount", "time"]
sample_req: List[str] = ["depth"]


required: Dict[str, List[str]] = {
    "Valve.1": valve_req,
    "Valve.2": valve_req,
    "Valve.3": valve_req,
    "Valve.Ethanol": valve_req,
    "FlowSensor": ["input", "ppl", "rate"],
    "Motor.Sample": motor_req,
    "Motor.Ethanol": motor_req,
    "Adc": ["bus", "addr"],
    "Pressure.Env": pressure_req,
    "Pressure.Filter": pressure_req + ["max"],
    "LED": ["gpio", "startdc", "startnumblinks", "depthdc", "successstatusdc",
            "unsuccessstatusdc"],
    "Collect.Sample": collect_req,
    "Collect.Ethanol": collect_req,
    "Sample.1": sample_req,
    "Sample.2": sample_req,
    "Sample.3": sample_req,
    "Deployment": ["seekerr", "deptherr", "prrate", "seektime"]
}


def quick_validate(cfg: Config):
    """
    Verify that all required configuration entries are present, raises
    a config.BadEntry exception if any are missing.
    """
    for k, vals in required.items():
        for val in vals:
            cfg.get_string(k, val)


def validate(cfg: Config) -> List[str]:
    """
    Verify that all required configuration entries are present, returns
    a list of all missing entries.
    """
    missing = []
    for k, vals in required.items():
        for val in vals:
            try:
                cfg.get_string(k, val)
            except BadEntry:
                missing.append("/".join([k, val]))
    return missing


def main():
    parser = argparse.ArgumentParser(description="Validate an eDNA deployment configuration")
    parser.add_argument("cfg", metavar="FILE",
                        nargs="?",
                        default="",
                        help="deployment configuration file")
    parser.add_argument("--sys", metavar="FILE",
                        default=os.path.expanduser("~/.config/edna/system.cfg"),
                        help="location of the system confguration file")
    args = parser.parse_args()

    try:
        cfg = Config(args.sys)
    except Exception as e:
        print("Error loading system config file; " + str(e), file=sys.stderr)
        return 1

    if args.cfg:
        try:
            cfg.load(args.cfg)
        except Exception as e:
            print("Error loading deployment config file; " + str(e), file=sys.stderr)
            return 1

    try:
        missing = validate(cfg)
        if missing:
            print("Missing entries: {}".format(";".join(missing)))
            return 1
    except Exception as e:
        print("Validation failed: {}".format(str(e)), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
