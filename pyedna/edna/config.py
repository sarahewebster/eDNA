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


class Config(object):
    """
    Class to parse the contents of one of more INI style configuration files.
    """
    def __init__(self, data: Any):
        """
        Create the parser and load the initial data. If data is either a
        filename (string) or a file-like object.
        """
        self.parser = ConfigParser(interpolation=ExtendedInterpolation())
        if isinstance(data, str):
            self.parser.read(data)
        else:
            self.parser.read_file(data)

    def load(self, filename: str):
        """
        Parse an additional configuration file.
        """
        self.parser.read([filename])

    def get_string(self, section: str, key: str) -> str:
        try:
            value = self.parser.get(section, key)
        except Error:
            raise BadEntry("/".join([section, key]))
        return value

    def get_int(self, section: str, key: str) -> int:
        try:
            value = self.parser.getint(section, key)
        except Error:
            raise BadEntry("/".join([section, key]))
        return value

    def get_float(self, section: str, key: str) -> float:
        try:
            value = self.parser.getfloat(section, key)
        except Error:
            raise BadEntry("/".join([section, key]))
        return value
