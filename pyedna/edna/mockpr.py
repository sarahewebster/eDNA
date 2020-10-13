# -*- coding: utf-8 -*-
"""
Mock the eDNA pressure sensors
"""
from random import normalvariate


def volts_to_counts(v: float, gain: float) -> int:
    vrange = 4.096/gain
    return int(v*32767.0/vrange)


class Adc(object):
    def __init__(self, *args, **kw):
        pass

    def read_adc(self, chan: int, gain: float) -> int:
        # 0.4v is approximately 10 psi
        if chan == 1:
            v = normalvariate(0.4, 0.025)
        else:
            v = normalvariate(1.2, 0.025)
        return volts_to_counts(v, gain)
