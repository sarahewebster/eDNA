# -*- coding: utf-8 -*-
"""
.. module:: edna.sample
     :platform: any
     :synopsis: eDNA data collection functions
"""
from . import periph, ticker
from collections import OrderedDict, namedtuple
from typing import Mapping, Any, List, Callable, Tuple, Optional
import datetime
import json
import time
import logging


# Type hint for data records
Record = Mapping[str, Any]

# flow_monitor stopping criteria
Limits = namedtuple('Limits', ['time', 'amount'])


class Timeout(Exception):
    pass


class DepthError(Exception):
    pass


class Datafile(object):
    """
    Class to implement a newline-delimited JSON data file.
    """
    def __init__(self, file):
        self.file = file

    def add_record(self, event: str, data: Record, ts: float = 0):
        """
        Append a record to the file. If the timestamp, ts, is zero, the
        current time is used.
        """
        if ts == 0:
            t = datetime.datetime.now(tz=datetime.timezone.utc)
        else:
            t = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
        rec = OrderedDict(t=t.isoformat(sep='T', timespec='milliseconds'),
                          event=event, data=data)
        self.file.write(json.dumps(rec) + "\n")


def read_battery(b: periph.Battery, tries: int = 4) -> Tuple[float, float, int]:
    """
    Return voltage, current, and state of charge from a Smart Battery. Multiple
    read attempts are made because the battery will return a NAK on the I2C
    bus if it is busy (rather than simply delaying its response).
    """
    v, a, soc = float(0), float(0), int(0)
    for i in range(tries):
        try:
            v = b.voltage()
            break
        except IOError:
            time.sleep(0.1)

    for i in range(tries):
        try:
            a = b.current()
            break
        except IOError:
            time.sleep(0.1)

    for i in range(tries):
        try:
            soc = b.charge()
            break
        except IOError:
            time.sleep(0.1)

    return v, a, soc


def flow_monitor(df: Optional[Datafile], event: str,
                 pump: int,
                 valve: periph.Valve, fm: periph.FlowMeter,
                 rate: float, stop: Limits,
                 checkpr: Callable[[], Tuple[float, bool]],
                 checkdepth: Callable[[], Tuple[float, bool]],
                 batts: List[periph.Battery] = []) -> Tuple[float, float, bool]:
    """
    Open a valve and run a flow meter until the requested amount of fluid is
    collected (stop.amount) or an error condition is met. The return value
    is a tuple of; total fluid amount in liters, elapsed time in seconds, and
    a boolean flag which is True if an overpressure condition was detected.

    Errors:
      - stop.time exceeded; raises a Timeout exception
      - checkdepth returns _, False; raises a DepthError exception

    :param df: data file or None
    :param event: tag for data file records
    :param pump: pump motor GPIO line
    :param valve: valve to open, will be closed on return
    :param fm: flow meter
    :param rate: flow meter sampling rate in Hz
    :param stop: sampling stop criteria
    :param checkpr: function to check the pressure across the filter
    :param checkdepth: function to check the depth
    """
    logger = logging.getLogger("edna.sample")
    period = 1./rate
    overpressure = False
    t_stop = time.time() + stop.time
    fm.reset()
    with valve:
        logger.info("Starting pump %d", pump)
        def cb_log():
            logger.info("Stopping pump %d", pump)
        with periph.gpio_high(pump, cb=cb_log):
            for tick in ticker(period):
                amount, secs = fm.amount()
                pr, pr_ok = checkpr()
                depth, depth_ok = checkdepth()
                if df is not None:
                    df.add_record(event, OrderedDict(elapsed=secs, amount=amount,
                                                     pr=pr, pr_ok=pr_ok,
                                                     depth=depth), ts=tick)
                if not overpressure:
                    overpressure = not pr_ok
                if amount >= stop.amount:
                    break
                if tick > t_stop:
                    break
                if not depth_ok:
                    raise DepthError()
            if df is not None:
                for i, b in enumerate(batts):
                    v, a, soc = read_battery(b)
                    df.add_record("battery-"+str(i),
                                  OrderedDict(v=v, a=a, soc=soc))

    return amount, secs, overpressure


SampleIdx: int = 0
EthanolIdx: int = 1

def collect(df: Datafile, index: int,
            pumps: Tuple[int],
            valves: Tuple[periph.Valve],
            fm: periph.FlowMeter,
            rate: float,
            limits: Tuple[Limits],
            checkpr: Callable[[], Tuple[float, bool]],
            checkdepth: Callable[[], Tuple[float, bool]],
            batts: List[periph.Battery] = []) -> bool:
    """
    Run a complete eDNA sample sequence.
    """
    logger = logging.getLogger("edna.sample")
    logger.info("Starting sample %d", index)
    try:
        vwater, w_secs, w_ovp = flow_monitor(df, "sample."+str(index),
                                             pumps[SampleIdx],
                                             valves[SampleIdx], fm,
                                             rate,
                                             limits[SampleIdx],
                                             checkpr,
                                             checkdepth, batts)

        if w_ovp:
            logger.warning("Overpressure event during sample pumping")
    except DepthError:
        logger.critical("Depth not maintained; sample %d aborted", index)
        return False

    vethanol, e_secs, e_ovp = flow_monitor(None, "",
                                           pumps[EthanolIdx],
                                           valves[EthanolIdx], fm,
                                           rate,
                                           limits[EthanolIdx],
                                           checkpr,
                                           lambda: (0.0, True), batts)
    if e_ovp:
        logger.warning("Overpressure event during ethanol pumping")

    df.add_record("result."+str(index),
                  OrderedDict(elapsed=w_secs+e_secs, vwater=vwater, vethanol=vethanol,
                              overpressure=(w_ovp or e_ovp)))
    return True
