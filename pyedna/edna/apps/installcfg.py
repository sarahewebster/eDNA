#!/usr/bin/env python3
"""
Install the eDNA system configuration file.
"""
import sys
import os
import os.path
import pkgutil
import argparse


def parse_cmdline() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install default eDNA system config file")
    parser.set_defaults(syscfg=os.environ.get("EDNA_SYSCFG", os.path.expanduser("~/.config/edna/system.cfg")))
    parser.add_argument("--syscfg", metavar="FILE",
                        help="location of the system confguration file")
    return parser.parse_args()


def main() -> int:
    args = parse_cmdline()
    text = pkgutil.get_data("edna", "resources/eDNA.cfg")
    if text is None:
        print("Configuration not found!", file=sys.stderr)
        return 1
    os.makedirs(os.path.dirname(args.syscfg), exist_ok=True)
    with open(args.syscfg, "wb") as f:
        f.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
