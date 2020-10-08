"""
eDNA sampling functions
"""
from . import periph
from collections import OrderedDict, namedtuple
from typing import Mapping, Any, List, Callable, Tuple
import datetime
import json
import time


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

    def add_record(self, event: str, data: Record, t: datetime.datetime = None):
        """
        Append a record to the file.
        """
        if t is None:
            t = datetime.datetime.now(tz=datetime.timezone.utc)
        rec = OrderedDict(t=t.isoformat(sep='T', timespec='milliseconds'),
                          event=event, data=data)
        self.file.write(json.dumps(rec) + "\n")


def read_battery(b: periph.Battery) -> Tuple[float, float, float]:
    try:
        v = b.voltage()
    except IOError:
        try:
            v = b.voltage()
        except IOError:
            v = 0
    try:
        ma = b.current()
    except IOError:
        try:
            ma = b.current()
        except IOError:
            ma = 0
    try:
        soc = b.charge()
    except IOError:
        try:
            soc = b.charge()
        except IOError:
            soc = 0
   return v, ma, soc


def flow_monitor(df: Datafile, event: str, valve: periph.Valve, cntr: periph.Counter,
                 scale: float, rate: float, stop: Limits,
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

    @param df: data file
    @param event: tag for data file records
    @param valve: valve to open, will be closed on return
    @param cntr: flow meter pulse counter
    @param scale: flow meter liters per pulse
    @param rate: flow meter sampling rate in Hz
    @param stop: sampling stop criteria
    @param checkpr: function to check the pressure across the filter
    @param checkdepth: function to check the depth
    @param batts: list of batteries to check during a sample
    """
    period = 1./rate
    overpressure = False
    cntr.reset()
    with valve:
        while True:
            counts, secs = cntr.read()
            amount = counts*scale
            pr, pr_ok = checkpr()
            depth, depth_ok = checkdepth()
            df.add_record(event, OrderedDict(elapsed=secs, amount=amount,
                                             pr=pr, pr_ok=pr_ok, depth=depth))
            if not overpressure:
                overpressure = not pr_ok
        for i, b in enumerate(batts):
            v, ma, soc = read_battery(b)
            df.add_record("battery-"+str(i),
                          OrderedDict(v=v, ma=ma, soc=soc))
        if amount >= stop.amount:
            return amount, secs, overpressure
        if secs > stop.time:
            raise Timeout()
        if not depth_ok:
            raise DepthError()
        time.sleep(period)
