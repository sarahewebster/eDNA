# -*- coding: utf-8 -*-
"""
.. module:: edna.config
     :platform: any
     :synopsis: eDNA configuration file parser
"""
from configparser import ConfigParser, ExtendedInterpolation, Error
from typing import Any, List, Dict


# Required keys for various sections
valve_req: List[str] = ["enable", "in1", "in2"]
motor_req: List[str] = ["enable"]
pressure_req: List[str] = ["chan", "gain", "coeff"]
collect_req: List[str] = ["amount", "time"]
sample_req: List[str] = ["depth"]


# Required sections and keys
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
    "LED": ["gpio"],
    "Collect.Sample": collect_req,
    "Collect.Ethanol": collect_req,
    "Sample.1": sample_req,
    "Sample.2": sample_req,
    "Sample.3": sample_req,
    "Deployment": ["seekerr", "deptherr", "prrate", "seektime"]
}


class BadEntry(Exception):
    def __init__(self, key, msg=""):
        self.key = key
        self.msg = msg

    def __str__(self):
        return "Configuration error; '{}': {}".format(self.key, self.msg)


class Config(ConfigParser):
    """
    Class to parse the contents of one of more INI style configuration files.
    """
    def __init__(self, data: Any):
        """
        Create the parser and load the initial data. If data is either a
        filename (string) or a file-like object.
        """
        super().__init__(interpolation=ExtendedInterpolation())
        self.load(data)

    def load(self, data: Any):
        """
        Parse an additional configuration file.
        """
        if isinstance(data, str):
            self.read(data)
        else:
            self.read_file(data)

    def validate(self) -> List[str]:
        """
        Verify that all required configuration entries are present, returns
        a list of all missing entries.
        """
        missing = []
        for k, vals in required.items():
            for val in vals:
                try:
                    self.get_string(k, val)
                except BadEntry:
                    missing.append("/".join([k, val]))
        return missing

    def get_string(self, section: str, key: str) -> str:
        """
        Return a configuration entry.
        """
        try:
            value = self.get(section, key)
        except Error:
            raise BadEntry("/".join([section, key]))
        return value

    def get_int(self, section: str, key: str) -> int:
        s = self.get_string(section, key)
        try:
            value = int(s, base=0)
        except ValueError:
            raise BadEntry("/".join([section, key]))
        return value

    def get_expr(self, section: str, key: str) -> Any:
        s = self.get_string(section, key)
        return eval(s)

    def get_float(self, section: str, key: str) -> float:
        try:
            value = self.getfloat(section, key)
        except Error:
            raise BadEntry("/".join([section, key]))
        return value

    def get_array(self, section: str, key: str) -> List[float]:
        s = self.get_string(section, key)
        f = []
        try:
            for val in s.split(","):
                f.append(float(val.strip()))
        except ValueError:
            raise BadEntry("/".join([section, key]))
        return f
