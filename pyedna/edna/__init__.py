import time
try:
    from importlib import metadata # type: ignore
except ImportError:
    # Running on pre-3.8 Python; use importlib-metadata package
    import importlib_metadata as metadata # type: ignore

__version__ = metadata.version(__name__)


def ticker(interval, fsleep=time.sleep):
    """
    Timer tick generator. Can be used to iterate at a fixed rate.
    Returns a series of time values.

    @param interval: time between ticks in seconds
    @param fsleep: sleep function
    """
    t0 = time.time()
    while True:
        t1 = time.time()
        yield t1
        if interval > 0:
            t0 += interval
            if t0 < t1:
                t0 = t1
            fsleep(t0 - t1)
        else:
            break
