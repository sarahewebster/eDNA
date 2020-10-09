# -*- coding: utf-8 -*-
"""
.. module:: edna.periph
     :platform: Linux (Raspberry Pi)
     :synopsis: interface to hardware peripherals
"""
try:
    import RPi.GPIO as GPIO # type: ignore
except ImportError:
    import edna.mockgpio as GPIO
import time
import logging
from typing import Tuple, Any


logging.getLogger("edna").addHandler(logging.NullHandler())


class Counter(object):
    """
    Class to count state transitions on a GPIO input line
    """
    t0: float
    t: float
    count: int
    line: int
    name: str

    def __init__(self, line: int, name: str):
        """
        :param line: GPIO line to monitor
        """
        self.line = line
        self.name = name
        self.logger = logging.getLogger("edna.counter")
        GPIO.setup(self.line, GPIO.IN)
        self.reset()

    def __del__(self):
        GPIO.remove_event_detect(self.line)

    def __str__(self):
        return self.name

    def reset(self):
        try:
            GPIO.remove_event_detect(self.line)
        except Exception:
            pass
        self.count = 0
        self.t0 = time.time()
        self.t = 0
        GPIO.add_event_detect(self.line, GPIO.RISING, callback=self._cb)
        self.logger.info("Counter %s reset", self.name)

    def _cb(self):
        self.count += 1
        self.t = time.time() - self.t0

    def read(self)-> Tuple[int, float]:
        """
        Return a tuple of the transition count and elapsed time.
        """
        return self.count, self.t


class FlowMeter(Counter):
    """
    Class to implement a flow meter from a digital pulse counter.
    """
    def __init__(self, line: int, ppl: int):
        """
        :param line: GPIO line to monitor
        :param ppl: pulses per liter
        """
        self.scale = 1./float(ppl)
        super().__init__(line, "flowmeter")

    def amount(self) -> Tuple[float, float]:
        pulses, t = self.read()
        return float(pulses)*self.scale, t


class Valve(object):
    """
    Class to represent a solenoid valve. This class is a Context Manager
    which allows the following usage:

        with Valve(enable, pwr, gnd):
            do_something()

    The valve will be open within the Context and closed when it exits.
    """
    def __init__(self, enable: int, power: int, ground: int):
        """
        :param enable: GPIO line to select this valve
        :param power: power GPIO line
        :param ground: ground GPIO line
        """
        self.enable = enable
        self.power = power
        self.ground = ground
        self.logger = logging.getLogger("edna.valve")

    def __str__(self):
        return "Valve({:d}, {:d}, {:d})".format(self.enable, self.power, self.ground)

    def _setup(self):
        GPIO.setup([self.enable, self.power, self.ground], GPIO.OUT)

    def open(self):
        """
        Open the valve
        """
        self._setup()
        GPIO.output(self.enable, GPIO.HIGH)
        GPIO.output([self.power, self.ground], (GPIO.HIGH, GPIO.LOW))
        self.logger.info("%s opened", str(self))

    def close(self):
        """
        Close the valve.
        """
        self._setup()
        GPIO.output(self.enable, GPIO.HIGH)
        GPIO.output([self.power, self.ground], (GPIO.LOW, GPIO.HIGH))
        self.logger.info("%s closed", str(self))

    def __enter__(self):
        """
        Context Manager support
        """
        self.open()
        return self

    def __exit__(self, etype, val, traceback):
        self.close()
        # Allow exceptions to propogate out
        return False


class Battery(object):
    """
    Class to represent a Smart Battery controller on an I2C bus.
    """
    # Command message codes from the Smart Battery specification
    msgs = {
        "voltage": 0x09,
        "current": 0x0a,
        "charge": 0x0e
    }
    # Smart Batteries all have the same I2C address
    bus_addr = 0x0b

    def __init__(self, bus: Any):
        """
        :param bus: the I2C (SMbus) interface
        :type bus: smbus.SMBus or smbus2.SMBus
        """
        self.bus = bus

    def voltage(self) -> float:
        """
        Return battery voltage in volts
        """
        val = self.bus.read_i2c_block_data(self.bus_addr, self.msgs["voltage"], 2)
        return float((val[0] + val[1]*256.)/1000.)

    def current(self) -> int:
        """
        Return battery current in mA. A positive value means the battery
        is charging, negative means discharging.
        """
        val = self.bus.read_i2c_block_data(self.bus_addr, self.msgs["current"], 2)
        ma = val[0] + val[1]*256
        # Convert to a signed 16-bit value
        if ma & 0x8000:
            ma = ma - 0x10000
        return ma

    def charge(self) -> int:
        """
        Return the battery charge state as a percentage.
        """
        val = self.bus.read_i2c_block_data(self.bus_addr, self.msgs["charge"], 2)
        return val[0] + val[1]*256


def read_pressure(adc: Any, chan: int, gain: float=2/3) -> float:
    """
    Read pressure from an AdaFruit ADS1x15 ADC channel and return
    the value in psia.

    :param adc: ADC object
    :type adc: Adafruit_ADS1x15
    :param chan: channel number
    :param gain: ADC gain setting
    """
    x = adc.read_adc(chan, gain)
    v = 6.144*x/32767.0
    return 50.0*v - 10


def psia_to_dbar(p: float) -> float:
    """
    Convert a pressure value from psia to decibars relative to the
    water surface.
    """
    return (p - 14.7)*0.689476
