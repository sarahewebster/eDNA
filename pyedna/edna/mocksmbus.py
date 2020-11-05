# -*- coding: utf-8 -*-
"""
Mock an SMBus interface for the eDNA Smart Batteries
"""
from typing import List
import logging
from random import randint


class SMBus(object):
    def __init__(self, bus: int):
        self.bus = bus

    def read_i2c_block_data(self, addr: int, reg: int, n: int) -> List[int]:
        logging.getLogger("smbus").info("Read SMBus(%d, %x) register %x",
                                        self.bus, addr, reg)
        if randint(1, 5) == 3:
            raise IOError()
        return [int(1)] * n
