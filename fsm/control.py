import time
from thread import start_new_thread

from common.robot import RobotRef
from common.amap import MapRefWithBuffer,MapRef
from common.timer import timed_call
from common.debug import debug,DEBUG_STATES
from fsm.states import ReadyState
from fsm.machine import *
from algorithms.shortest_path import *



class CentralController(StateMachine):
    """
    run control_task method to start running the controller
    """

    _input_q = None # input queue
    _cmd_out_q = None
    _data_out_qs = None # list of queue

    def control_task(self):
        "central control"
        # init robot
        while True:
            if (not self._input_q.empty()):
                input_tuple = self._input_q.get_nowait()
                if (not input_tuple): continue
                cmd_list,data_list = self._state.process_input(input_tuple[0],input_tuple[1])
                if (cmd_list):
                    self._enqueue_list(self._cmd_out_q,cmd_list,True)
                if (data_list):
                    for q in self._data_out_qs:
                        self._enqueue_list(q,data_list)

    def set_next_state(self,state):
        debug("Next state set to {}".format(str(state)),DEBUG_STATES)
        for q in self._data_out_qs:
            self._enqueue_list(q=q,list=[PMessage(type=PMessage.T_STATE_CHANGE,msg=str(state))])
        self._state = state

    def reset(self):
        # state must be init after map_ref and robot_ref
        self._map_ref = MapRefWithBuffer()
        self._robot_ref = RobotRef()
        self._state = ReadyState(machine=self)

    def __init__(self,input_q,cmd_out_q,data_out_qs):
        self._input_q = input_q
        self._cmd_out_q = cmd_out_q
        self._data_out_qs = data_out_qs
        self.reset()

    def update(self):
        pass

    def send_command(self,msg):
        try:
            pmsg = PMessage(type=PMessage.T_COMMAND,msg=msg)
            self._enqueue_list(self._cmd_out_q,[pmsg])
        except Exception,e:
            pass

    # allow delay is deprecated
    def _enqueue_list(self,q,list,allow_delay=False):
        "enqueue list items on another thread"
        start_new_thread(self._enqueue_list_internal,(q,list,allow_delay,))

    def _enqueue_list_internal(self,q,list,allow_delay=False):
        "thread task"
        for item in list:
            if (item):
                q.put_nowait(item)