from thread import start_new_thread
import time


class Timer():
    _time_limit = 0
    _interval = 1
    _interval_callback = None  # a function, accepting a single int as param
    _end_callback = None  # a function
    _is_timing = False

    def __init__(self, limit, interval=1, interval_callback=None, end_callback=None):
        self._time_limit = limit
        self._interval = interval
        self._interval_callback = interval_callback
        self._end_callback = end_callback

    def start(self):
        self._is_timing = True
        start_new_thread(self._internal_run, ())

    def _internal_run(self):
        t= self._time_limit
        while(t>0 and self._is_timing):
            if (self._interval_callback): self._interval_callback(t)
            time.sleep(self._interval)
            t -= 1
        if (self._end_callback): self._end_callback()
        self._is_timing = False

    def is_timing(self):
        return self._is_timing

    def shutdown(self):
        self._is_timing = False


def timed_call(func, **kwargs):
    "return function result, time_taken"
    start = time.time()
    result = func(**kwargs)
    end = time.time()
    return result, (end - start)