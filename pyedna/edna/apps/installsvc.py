#!/usr/bin/env python3
"""
Install the runedna Systemd service file
"""
import sys
import os
import os.path
import pkgutil
import argparse


def parse_cmdline() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install the runedna Systemd service file")
    parser.add_argument("--svcdir", metavar="DIR",
                        default=os.path.expanduser("~/.config/systemd/user"),
                        help="service file directory")
    return parser.parse_args()


def main() -> int:
    args = parse_cmdline()
    text = pkgutil.get_data("edna", "resources/runedna@.service")
    if text is None:
        print("File not found!", file=sys.stderr)
        return 1
    os.makedirs(args.svcdir, exist_ok=True)
    with open(os.path.join(args.svcdir, "runedna@.service"), "wb") as f:
        f.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
