# -*- coding: utf-8 -*-
"""
.. module:: edna.periph
     :platform: Linux (Raspberry Pi)
     :synopsis: interface to hardware peripherals
"""
try:
    import RPi.GPIO as GPIO # type: ignore
except ImportError:
    import edna.mockgpio as GPIO # type: ignore
import time
import logging
import queue
from threading import Thread, Event
from typing import Tuple, Any, Callable, Union, List
from contextlib import contextmanager
from . import ticker


logging.getLogger("edna").addHandler(logging.NullHandler())


@contextmanager
def gpio_high(line: int, cb: Callable[[], None] = None):
    GPIO.output(line, GPIO.HIGH)
    yield
    GPIO.output(line, GPIO.LOW)
    if cb is not None:
        cb()


class Counter(object):
    """
    Class to count state transitions on a GPIO input line
    """
    t0: float
    t: float
    count: int
    line: int
    name: str

    def __init__(self, line: int, name: str = ""):
        """
        :param line: GPIO line to monitor
        """
        self.line = line
        self.name = name or "Counter({:d})".format(line)
        self.logger = logging.getLogger("edna.counter")
        GPIO.setup(self.line, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
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
        self.logger.info("Counter '%s' reset", self.name)

    def _cb(self, *args):
        self.count += 1

    def read(self)-> Tuple[int, float]:
        """
        Return a tuple of the transition count and elapsed time.
        """
        return self.count, time.time() - self.t0


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
        super().__init__(line, "flow-meter")

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
    enable: int
    opened: bool
    _lopen: Union[int, None]
    _lclose: Union[int, None]

    def __init__(self, enable: int, in1: int, in2: int, lopen: str = "in1", lclose: str = "in2"):
        """
        :param enable: GPIO line to enable this valve
        :param in1: GPIO line connected to IN1
        :param in2: GPIO line connected to IN2
        :param lopen: H-bridge line which opens the valve
        :param lclose: H-bridge line which closes the valve
        """
        self.opened = False
        self.enable = enable
        self.logger = logging.getLogger("edna.valve")
        l = locals()
        self._lopen = l.get(lopen.lower())
        if self._lopen is None:
            raise ValueError("'{}': invalid valve control line".format(lopen))

        self._lclose = l.get(lclose.lower())
        if self._lclose is None:
            raise ValueError("'{}': invalid valve control line".format(lclose))

        GPIO.setup([self.enable, self._lopen, self._lclose], GPIO.OUT)
        GPIO.output(self.enable, GPIO.HIGH)
        self.close()

    def __str__(self):
        return "Valve({:d}, {:d}, {:d})".format(self.enable, self._lopen, self._lclose)

    def isopened(self) -> bool:
        return self.opened

    def open(self):
        """
        Open the valve
        """
        GPIO.output(self._lclose, GPIO.LOW)
        GPIO.output(self._lopen, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(self._lopen, GPIO.LOW)
        self.opened = True
        self.logger.info("%s opened", str(self))

    def close(self):
        """
        Close the valve.
        """
        GPIO.output(self._lopen, GPIO.LOW)
        GPIO.output(self._lclose, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(self._lclose, GPIO.LOW)
        self.opened = False
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

    def current(self) -> float:
        """
        Return battery current in amps. A positive value means the battery
        is charging, negative means discharging.
        """
        val = self.bus.read_i2c_block_data(self.bus_addr, self.msgs["current"], 2)
        ma = val[0] + val[1]*256
        # Convert to a signed 16-bit value
        if ma & 0x8000:
            ma = ma - 0x10000
        return float(ma)/1000.

    def charge(self) -> int:
        """
        Return the battery charge state as a percentage.
        """
        val = self.bus.read_i2c_block_data(self.bus_addr, self.msgs["charge"], 2)
        return val[0] + val[1]*256


class PrSensor(object):
    """
    Class to implement a pressure sensor attached to an Adafruit_ADS1x15
    ADC board.
    """
    adc: Any
    chan: int
    gain: float
    vmax: float
    vbase: float = 4.096

    def __init__(self, adc: Any, chan: int, gain: float,
                 coeff: List[float] = [-10., 50.]):
        """
        :param adc: ADC object
        :param chan: channel number
        :param gain: gain value
        :param coeff: coefficients to convert volts to psi

        The equation to convert volts to psi is:

            psi = coeff[0] + coeff[1]*volts
        """
        self.adc = adc
        self.gain = gain
        self.vmax = self.vbase/gain
        self.chan = chan
        self.coeff = coeff

    def read_volts(self) -> float:
        """
        Return the sensor value in volts.
        """
        x = self.adc.read_adc(self.chan, self.gain)
        return self.vmax*x/32767.0

    def read(self) -> float:
        """
        Return the sensor value in psi
        """
        return self.coeff[0] + self.read_volts()*self.coeff[1]

    def read_burst(self, n: int, interval: float) -> float:
        """
        Return the mean of n values sampled interval seconds apart.
        """
        v = 0.
        self.adc.start_adc(self.chan, gain=self.gain)
        try:
            i = 0
            for tick in ticker(interval):
                alpha = 1./float(i + 1)
                beta = 1. - alpha
                x = self.adc.get_last_result()
                v = alpha*self.vmax*x/32767.0 + beta*v
                i += 1
                if i >= n:
                    break
        finally:
            self.adc.stop_adc()
        return self.coeff[0] + v*self.coeff[1]


class Integrator(object):
    """
    Class to integrate an analog signal input to an an Adafruit_ADS1x15 A/D converter.
    """
    adc: Any
    ev: Event
    tid: Any
    chan: int
    gain: float
    vmax: float
    t0: float = 0
    fncvt: Any
    vbase: float = 4.096

    def __init__(self, adc: Any, chan: int, gain: float,
                 fncvt: Any):
        """
        :param adc: ADC object
        :param chan: channel number
        :param gain: gain value
        :param fncvt: function to convert ADC voltage to
                      the value to integrate
        """
        self.logger = logging.getLogger("integrator")
        self.adc = adc
        self.gain = gain
        self.chan = chan
        self.fncvt = fncvt
        self.vmax = self.vbase/gain
        self.ev = Event()
        self.tid = None

    def _integrate(self, interval: float, q: queue.Queue):
        self.adc.start_adc(self.chan, gain=self.gain)
        sum = float(0.)
        try:
            for tick in ticker(interval):
                x = self.adc.get_last_result()
                v = self.vmax*x/32767.0
                sum += (self.fncvt(v) * interval)
                try:
                    q.put_nowait((sum, time.time() - self.t0))
                except queue.Full:
                    pass
                if self.ev.is_set():
                    break
        finally:
            self.adc.stop_adc()

    def start(self, period: float, q: queue.Queue):
        """
        Start a thread to sample and integrate the signal at the specified
        period and write the integral values to a Queue
        """
        if self.tid is not None:
            self.stop()
        self.tid = Thread(target=self._integrate,
                          args=(period, q), daemon=True)
        self.ev.clear()
        self.t0 = time.time()
        self.tid.start()
        self.logger.info("Start integrator; period = %.2fs", period)

    def stop(self):
        if self.tid is not None:
            self.ev.set()
            self.tid.join(timeout=2)
            self.tid = None
            self.logger.info("Stop integrator")


class AnalogFlowMeter(Integrator):
    """
    Class to represent a Renesas FS2012 flow sensor interfaced to an ADC channel
    """
    def __init__(self, adc: Any, chan: int, gain: float,
                 coeff: List[float]):
        def cvt(v: float) -> float:
            return coeff[0] + coeff[1]*v
        super().__init__(adc, chan, gain, cvt)


def psia_to_dbar(p: float) -> float:
    """
    Convert a pressure value from psia to decibars relative to the
    water surface.
    """
    return (p - 14.7)*0.689476


def psi_to_dbar(p: float) -> float:
    """
    Convert a gauge pressure value from psi to decibars.
    """
    return p*0.689476


def sawtooth(count: int):
    """
    Generator to produce a sawtooth wave with amplitude 1.0

    :param count: wavelength in points
    """
    x = 0
    mid = float(count)/2.
    while True:
        if x <= mid:
            y = float(x)/mid
        else:
            y = float(count - x)/mid
        x += 1
        if x == count:
            x = 0
        yield y


class LED(object):
    """
    Class to control an LED attached to a GPIO line.
    """
    line: int
    ctlr: Union[GPIO.PWM, None]
    tid: Any
    ev: Event

    def __init__(self, line: int):
        self.line = line
        GPIO.setup(self.line, GPIO.OUT)
        self.tid = None
        self.ev = Event()
        self.logger = logging.getLogger("edna.led")
        self.ctlr = None

    def __del__(self):
        self.stop_fade()
        self.stop_blink()

    def start_blink(self, period: float):
        """
        Start blinking the LED with a 50% duty cycle. For best results, the
        period should be at least one second long.
        """
        self.ctlr = GPIO.PWM(self.line, 1./period)
        self.ctlr.start(50)
        self.logger.info("Start LED blinker; period = %.2fs", period)

    def stop_blink(self):
        """
        Stop the LED blinking.
        """
        if self.ctlr is not None:
            self.ctlr.stop()
            self.ctlr = None
            self.logger.info("Stop LED blinker")

    def _fader(self, period: float):
        rate = 0.1
        gen = sawtooth(int(period/rate))
        for tick in ticker(0.1):
            y = next(gen)
            if self.ctlr is not None:
                self.ctlr.ChangeDutyCycle(y*100)
            if self.ev.is_set():
                break

    def start_fade(self, period: float):
        """
        Start LED fade in/out. For best results, the period should be at
        least 5 seconds long.
        """
        if self.tid is not None:
            self.stop_fade()
        if self.ctlr is not None:
            self.ctlr.stop()
        self.ctlr = GPIO.PWM(self.line, 50)
        self.ctlr.start(0)
        self.tid = Thread(target=self._fader,
                          args=(period,), daemon=True)
        self.ev.clear()
        self.tid.start()
        self.logger.info("Start LED fader; period = %.2fs", period)

    def stop_fade(self):
        """
        Stop LED fade in/out
        """
        if self.tid is not None:
            self.ev.set()
            self.tid.join(timeout=2)
            self.tid = None
            self.ctrl.stop()
            self.ctrl = None
            self.logger.info("Stop LED fader")


@contextmanager
def blinker(led: LED, period: float):
    led.start_blink(period)
    yield
    led.stop_blink()


@contextmanager
def fader(led: LED, period: float):
    led.start_fade(period)
    yield
    led.stop_fade()


class Pump(object):
    """
    Class to represent a pump. This class is a Context Manager
    which allows the following usage:

        with Pump(line):
            do_something()

    The pump will be running within the Context and stopped when
    the Context exits.
    """
    def __init__(self, line: int):
        """
        :param line: GPIO line to enable this pump.
        """
        self.line = line
        self.logger = logging.getLogger("edna.pump")
        GPIO.setup(self.line, GPIO.OUT)

    def __str__(self):
        return "Pump({:d})".format(self.line)

    def start(self):
        """
        Start the pump
        """
        GPIO.output(self.line, GPIO.HIGH)
        self.logger.info("%s on", str(self))

    def stop(self):
        """
        Stop the pump
        """
        GPIO.output(self.line, GPIO.LOW)
        self.logger.info("%s off", str(self))

    def __enter__(self):
        """
        Context Manager support
        """
        self.start()
        return self

    def __exit__(self, etype, val, traceback):
        self.stop()
        # Allow exceptions to propogate out
        return False
