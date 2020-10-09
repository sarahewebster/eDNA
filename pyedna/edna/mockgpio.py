# -*- coding: utf-8 -*-
"""
Mock the Raspberry Pi GPIO interface.
"""
from . import ticker
import threading
import logging
from collections import namedtuple
from typing import Callable, Union, List, Dict, TypedDict, Any


logging.getLogger("gpio").addHandler(logging.NullHandler())


class State(object):
    type: int
    val: int
    thread: Any
    ev: Any
    def __init__(self, type=0, val=0, thread=None, ev=None):
        self.type = type
        self.val = val
        self.thread = thread
        self.ev = ev

_states: Dict[int, State] = dict()

BCM = 0
OUT = 1
IN = 0
HIGH = 1
LOW = 0
BOTH = 2


class Detector(threading.Thread):
    def __init__(self, cb: Callable[[None], None], ev: threading.Event, interval: float = 0.1):
        self.cb = cb
        self.interval = interval
        self.ev = ev
        super().__init__()
        self.daemon = True

    def run(self):
        for tick in ticker(self.interval):
            self.cb()
            if self.ev.is_set():
                break


def check_pin(pin: Union[int, List[int]], ptype: int):
    if isinstance(pin, int):
        if not pin in _states:
            raise KeyError("Pin {:d} not configured".format(pin))
        if _states[pin].type != ptype:
            raise TypeError("Pin {:d} type mismatch".format(pin))
    else:
        for p in pin:
            if not p in _states:
                raise KeyError("Pin {:d} not configured".format(p))
            if _states[p].type != ptype:
                raise TypeError("Pin {:d} type mismatch".format(p))


def setmode(mode: int):
    logging.getLogger("gpio").info("GPIO mode set")


def cleanup(*args):
    logging.getLogger("gpio").info("GPIO cleanup")


def add_event_detect(pin: int, which: int, callback: Callable[[None], None]):
    check_pin(pin, IN)
    ev = threading.Event()
    _states[pin].thread = Detector(callback, ev)
    _states[pin].ev = ev
    _states[pin].thread.start()
    logging.getLogger("gpio").info("Event detector started on pin %d", pin)


def remove_event_detect(pin: int):
    check_pin(pin, IN)
    _states[pin].ev.set()
    _states[pin].thread.join(timeout=1)
    logging.getLogger("gpio").info("Event detector stopped on pin %d", pin)


def setup(pin: Union[int, List[int]], ptype: int):
    if isinstance(pin, int):
        _states[pin] = State(val=0, type=ptype, thread=None, ev=None)
    else:
        for p in pin:
            _states[p] = State(val=0, type=ptype, thread=None, ev=None)


def output(pin: Union[int, List[int]], val: int):
    check_pin(pin, OUT)
    if isinstance(pin, int):
        _states[pin].val = val
    else:
        for p in pin:
            _states[p].val = val
    logging.getLogger("gpio").info("Output %d on %r", val, pin)


def input(pin: int) -> int:
    check_pin(pin, IN)
    logging.getLogger("gpio").info("Read pin %d", pin)
    return _states[pin].val
