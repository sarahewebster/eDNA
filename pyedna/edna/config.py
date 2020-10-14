# -*- coding: utf-8 -*-
"""
.. module:: edna.config
     :platform: any
     :synopsis: eDNA configuration file parser
"""
from configparser import ConfigParser, ExtendedInterpolation, Error
from typing import Any


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

    def get_string(self, section: str, key: str) -> str:
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

    def get_float(self, section: str, key: str) -> float:
        try:
            value = self.getfloat(section, key)
        except Error:
            raise BadEntry("/".join([section, key]))
        return value
