from threading import Thread
import time
import uuid
from common.debug import debug,DEBUG_TIMER
from common.utils import get_or_exception
from common.popattern import BaseObserver

class TimerThread(Thread):

    _time_limit = None
    _remaining_time = None
    _interval_callback = None # function
    _interval = None # int
    _end_callback = None
    _is_timing = None # boolean
    _name = ""

    def __init__(self,*args,**kwargs):
        """
        necessary params: `time_limit`,
        optional params: `interval_callback`, `end_callback`
        """
        super(TimerThread,self).__init__()
        self._time_limit = get_or_exception(kwargs,"time_limit",err_msg="time_limit must be passed in")
        self._remaining_time =0
        self._interval = 1
        self._interval_callback = kwargs.get("interval_callback")
        self._end_callback = kwargs.get("end_callback")
        self._is_timing = False
        self._name = str(uuid.uuid4())[:4]

    def run(self):
        debug("{} timer starts".format(self._name),DEBUG_TIMER)
        self._remaining_time= self._time_limit
        self._is_timing = True
        while(self._remaining_time>0 and self._is_timing):
            debug("{} timer remaining time: {}".format(self._name,self._remaining_time),DEBUG_TIMER)
            if (self._interval_callback): self._interval_callback(self._remaining_time)
            time.sleep(self._interval)
            self._remaining_time -= 1
        if (self._end_callback and self._remaining_time==0):
            debug("{} timer times up!".format(self._name),DEBUG_TIMER)
            self._end_callback()
        else:
            debug("{} timer forced to stop! remaining time: {}".format(self._name,self._remaining_time),DEBUG_TIMER)
        self._is_timing = False

    def is_timing(self):
        return self._is_timing

    def stop(self):
        self._is_timing = False

    def get_remaining_time(self):
        return self._remaining_time

    def get_time_passed(self):
        return self._time_limit - self._remaining_time

class Timer(object):

    _limit = None
    _interval_callback = None
    _end_callback = None
    _thread = None
    _id = None

    def __init__(self,*args,**kwargs):
        self._limit = get_or_exception(kwargs,"limit")
        self._interval_callback = kwargs.get("interval_callback",None)
        self._end_callback = kwargs.get("end_callback",None)
        self._thread = TimerThread(time_limit=self._limit,interval_callback=self._interval_callback,end_callback=self._end_callback)
        self._thread.daemon = True

    def start(self):
        self._thread.stop()
        self._thread = TimerThread(time_limit=self._limit,interval_callback=self._interval_callback,end_callback=self._end_callback)
        self._thread.daemon = True
        self._thread.start()

    def is_timing(self):
        return self._thread and self._thread.is_timing()

    def shutdown(self):
        self._thread.stop()

    def get_remaining_time(self):
        return self._thread.get_remaining_time()

    def get_time_passed(self):
        return self._thread.get_time_passed()


class ObserverTimer(Timer,BaseObserver):
    """
    a timer with update function
    """
    _update_call = None # function

    def __init__(self,*args,**kwargs):
        super(ObserverTimer,self).__init__(*args,**kwargs)
        self._update_call = kwargs.get("update_call",None)

    def update(self,data=None):
        if (self._update_call and hasattr(self._update_call,"__call__")):
            self._update_call()
        else:
            self.default_update_call()

    def default_update_call(self):
        if (self.is_timing()):
            self.shutdown()

def timed_call(func,**kwargs):
    "return function result, time_taken"
    start = time.time()
    result = func(**kwargs)
    end = time.time()
    return result,(end-start)