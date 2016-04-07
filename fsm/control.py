import time
from thread import start_new_thread

from common.robot import RobotRef,RobotRefWithMemory
from common.amap import MapRefWithBuffer,MapRef,MapSetting
from common.popattern import BaseObserver
from common.timer import timed_call
from common.debug import debug,DEBUG_STATES
from fsm.states import ReadyState
from fsm.machine import *
from algorithms.shortest_path import *


class CentralController(StateMachine):
    """
    This is a Singleton class
    run control_task method to start running the controller
    """

    _input_q = None # input queue
    _cmd_out_q = None
    _data_out_qs = None # list of queue
    _instance = None

    @staticmethod
    def get_instance(*args,**kwargs):
        if (not CentralController._instance):
            CentralController._instance = CentralController(*args,**kwargs)
        return CentralController._instance

    def control_task(self):
        "central control"
        #TODO: init listeners
        self._map_listener = MapUpdateListener(map_ref=self._map_ref)
        self._robot_listener = RobotUpdateListener(robot_ref=self._robot_ref)
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
        self._robot_ref = RobotRefWithMemory()
        self._state = ReadyState(machine=self)

    def __init__(self,*args,**kwargs):
        self._input_q = kwargs.get("input_q")
        self._cmd_out_q = kwargs.get("cmd_out_q")
        self._data_out_qs = kwargs.get("data_out_qs")
        self.reset()

    def update(self):
        pass

    def send_command(self,msg):
        try:
            pmsg = PMessage(type=PMessage.T_COMMAND,msg=msg)
            self._enqueue_list(self._cmd_out_q,[pmsg])
        except Exception,e:
            print("Exception in sending command:{}".format(e))

    def send_data_pmsg(self,pmsg):
        for q in self._data_out_qs:
            self._enqueue_list(q,[pmsg])

    def send_cmd_pmsg(self,pmsg):
        self._enqueue_list(self._cmd_out_q,[pmsg])

    # allow delay is deprecated
    def _enqueue_list(self,q,list,allow_delay=False):
        "enqueue list items on another thread"
        # start_new_thread(self._enqueue_list_internal,(q,list,allow_delay,))
        for item in list:
            if (item):
                q.put_nowait(item)


class MapUpdateListener(BaseObserver):
    """
    `_map_ref`
    `_controller`
    """
    _LAST_MSG = ''

    def __init__(self,*args,**kwargs):
        super(MapUpdateListener,self).__init__(*args,**kwargs)
        map_ref = kwargs.get("map_ref")
        map_ref.add_change_listener(self)
        self._map_ref = map_ref
        self._controller = CentralController.get_instance()

    def update(self,data=None):
        cleaned_data=[(x,y) for x,y in data if not self._map_ref.is_out_of_arena(x,y)]
        if (cleaned_data):
            message = "|".join(["{},{},{}".format(x,y,self.format_cell_value(x,y))
                                          for x,y in cleaned_data])
            if (message!=self._LAST_MSG):
                self._controller.send_data_pmsg(PMessage(type=PMessage.T_UPDATE_MAP_STATUS,
                            msg=message))
                self._LAST_MSG = message

    def format_cell_value(self,x,y):
        if (self._map_ref.get_cell(x,y)==MapSetting.OBSTACLE):
            return 1
        else:
            return 0

class RobotUpdateListener(BaseObserver):
    """
    `_robot_ref`
    `_controller`
    """

    def __init__(self,*args,**kwargs):
        super(RobotUpdateListener,self).__init__(*args,**kwargs)
        robot_ref = kwargs.get("robot_ref")
        robot_ref.add_change_listener(self)
        self._robot_ref = robot_ref
        self._controller = CentralController.get_instance()

    def update(self,data=None):
        x,y = self._robot_ref.get_position()
        o = self._robot_ref.get_orientation().get_value()
        self._controller.send_data_pmsg(PMessage(type=PMessage.T_UPDATE_ROBOT_STATUS,
                            msg="{},{},{}".format(x,y,o)))
