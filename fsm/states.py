"""
module for implementing Finite State Machine
"""
import os
from abc import ABCMeta,abstractmethod
import time
from thread import start_new_thread
from common import *
from common.timer import Timer
from middlewares import *
from machine import *
from common.pmessage import PMessage
from common.amap import MapSetting
from algorithms.shortest_path import AStarShortestPathAlgo
from algorithms.maze_explore import MazeExploreAlgo

class BaseState(object):

    _machine = None
    _map_ref = None # MapRef object, obtained from machine
    _robot_ref = None # RobotRef object, obtained from machine
    _middlewares = None # list of Middleware object

    def __init__(self,machine,**kwargs):
        self._machine = machine
        self._map_ref = self._machine.get_map_ref()
        self._robot_ref = self._machine.get_robot_ref()
        self._middlewares = []
        # init default middleware
        self._ack_mid = AckMiddleware(state=self)
        self.add_middleware(self._ack_mid)

    def add_middleware(self,mid_ware):
        self._middlewares.append(mid_ware)

    def clear_middlewares(self):
        self._middlewares = []

    def add_expected_ack(self,label,msg,call_back,args=None):
        #TODO: type check
        self._ack_mid.add_expected_ack(label=label,msg=msg,call_back=call_back,args=args)

    @abstractmethod
    def post_process(self,label,msg):
        """
        :return: a list of command Message and a list of data Message
        can call machine.set_next_state() to trigger state transition
        """
        raise NotImplementedError()

    def transit_state(self,new_state_cls):
        "new_state is State class"
        self._machine.set_next_state(new_state_cls(machine=self._machine))

    def reset_machine(self):
        self._machine.reset()
        self.transit_state(ReadyState)

    def process_input(self,label,msg):
        "process using middleware"
        cmd_ls,data_ls = [],[]
        for mid_ware in self._middlewares:
            try:
                cmds,datas = mid_ware.process(label,msg)
            except:
                continue
            cmd_ls = cmd_ls + cmds
            data_ls = data_ls + datas
            # stop processing when this mid does return something and it wants to consume the input
            if (mid_ware.is_consume_input() and (cmds or datas)):
                return cmd_ls,data_ls
        # call final processing function
        try:
            cmds,datas = self.post_process(label,msg)
            return cmd_ls+cmds,data_ls+datas
        except:
            return cmd_ls,data_ls

    def get_map_ref(self):
        return self._map_ref

    def get_robot_ref(self):
        return self._robot_ref

class ReadyState(BaseState):

    def __init__(self,*args,**kwargs):
        super(ReadyState,self).__init__(*args,**kwargs)
        self.clear_middlewares()
        self.add_middleware(MoveCommandMiddleware(state=self))
        self.add_middleware(MapUpdateMiddleware(state=self))

    def __str__(self):
        return "ReadyState"

    def post_process(self,label,msg):
        "only listen for explore, fast run and move commands"
        type,msg = label,msg
        # read android command
        if (msg.get_type()==PMessage.T_COMMAND):
            if (msg.get_msg()==PMessage.M_START_EXPLORE):
                self.transit_state(ExplorationState)
                return [msg],[PMessage(type=PMessage.T_STATE_CHANGE,msg=msg.get_msg())]

            elif(msg.get_msg()==PMessage.M_END_EXPLORE):
                self.transit_state(ExplorationDoneState)
        #TODO: load map from file, for simulation only
        elif(msg.get_type()==PMessage.T_LOAD_MAP):
            path = msg.get_msg()
            self._map_ref.load_map_from_file(path)
            return [],[]
        elif(msg.get_type()==PMessage.T_SET_ROBOT_POS):
            x,y=msg.get_msg().split(",")
            self._robot_ref.set_position((int(x),int(y)))
            return [PMessage(type=PMessage.T_SET_ROBOT_POS,msg=msg.get_msg())],[]
        return [],[]


class ExplorationState(StateMachine,BaseState):
    """
    This state contains three substates: ExplorationFirstRound, ExplorationSecondRount, ExplorationThirdRound
    Will make change to RobotRef and MapRef
    """

    def __init__(self,machine,**kwargs):
        super(ExplorationState,self).__init__(machine,**kwargs)
        self._map_ref = self._machine.get_map_ref()
        self._robot_ref = self._machine.get_robot_ref()
        self.set_next_state(ExplorationFirstRoundState(machine=self))
        self.clear_middlewares()
        self.add_middleware(MapUpdateMiddleware(state=self))

    def __str__(self):
        return "explore"

    def post_process(self,label,msg):
        type,msg = label,msg
        # android "end explore" command
        if (type in CMD_SOURCES and msg.get_type()==PMessage.T_COMMAND and msg.get_msg()==PMessage.M_END_EXPLORE):
            self.end_exploration()
            return [msg],[]

        cmd_list,data_list = self._state.process_input(label=label,msg=msg)
        return cmd_list,data_list

    def end_exploration(self):
        self._map_ref.save_map_to_file("temp.bin")
        self._machine.set_next_state(ExplorationDoneState(machine=self._machine))

class ExplorationFirstRoundState(BaseState):
    """
    Substate of ExplorationState
    Explore along the wall,only return commands and robot move update
    will change robotRef
    """
    _explore_algo = None
    _end_coverage_threshold = 60 #TODO: this is hardcoded

    def __init__(self,machine,**kwargs):
        super(ExplorationFirstRoundState,self).__init__(machine=machine,**kwargs)
        self._explore_algo = MazeExploreAlgo(robot=self._machine.get_robot_ref(),map_ref=self._machine.get_map_ref())

    def post_process(self,label,msg):
        # get next move
        if (label==ARDUINO_LABEL and msg.is_map_update()):
            command = self._explore_algo.get_next_move()
            if(self._robot_ref.get_position()==self._map_ref.get_start_zone_center_pos() and 100-self._map_ref.get_unknown_percentage()>self._end_coverage_threshold):
                self._machine.end_exploration()
            self.add_robot_move_to_be_ack(command)
            return [PMessage(type=PMessage.T_COMMAND,msg=command)],\
                   []

    def add_robot_move_to_be_ack(self,move):
        self.add_expected_ack(label=ARDUINO_LABEL,msg=PMessage(type=PMessage.T_ROBOT_MOVE,msg=move),call_back=self.ack_move_to_android,args=[move])

    def ack_move_to_android(self,move):
        self._robot_ref.execute_command(move)
        self._map_ref.set_fixed_cells(self._robot_ref.get_occupied_postions(),MapSetting.CLEAR)
        return [],[PMessage(type=PMessage.T_ROBOT_MOVE,msg=move)]

#TODO: this class is currently unused
class ExplorationSecondRoundState(BaseState):
    """
    Substate of ExplorationState
    Explore whatever hasn't been explored
    will change robotRef
    """
    def post_process(self,label,msg):
        #TODO: make the robot explore unexplored area
        self.transit_state(ExplorationGoBackState)
        return [],[]

#TODO: this class is currently unused
class ExplorationGoBackState(BaseState):
    """
    Substate of ExplorationState
    for going back to start position
    machine must be ExplorationState object
    no change to robotRef and mapRef
    """
    _cmd_buffer = []
    started_go_back = False

    def post_process(self,label,msg):
        if (self.is_going_back_finished()):
            self._machine.end_exploration()
            return [],[]
        else:
            if (not self.is_on_going_back()):
                self.started_go_back = True
                self._cmd_buffer = self.get_go_back_cmd_list()
            move = self.dequeue_buffer()
            self._robot_ref.execute_command(move)
            self._machine.add_robot_move_to_be_ack(move)
            return [PMessage(type=PMessage.T_COMMAND,msg=move)],[]#[PMessage(type=PMessage.T_ROBOT_MOVE,msg=move)]

    def is_going_back_finished(self):
        return self.started_go_back==True and not self._cmd_buffer

    def is_on_going_back(self):
        return self.started_go_back==True and self._cmd_buffer

    def get_go_back_cmd_list(self):
        map_ref = self._map_ref
        target_pos = map_ref.get_start_zone_center_pos()
        algo =AStarShortestPathAlgo(map_ref=map_ref,target_pos=target_pos)
        return algo.get_shortest_path(robot_ori=self._robot_ref.get_orientation(),robot_pos=self._robot_ref.get_position())

    def dequeue_buffer(self):
        if (not self._cmd_buffer): raise Exception("buffer is empty, cannot dequeue")
        to_return = self._cmd_buffer[0]
        self._cmd_buffer = self._cmd_buffer[1:]
        return to_return

class ExplorationDoneState(BaseState):
    """
    only accept start fast run command from android
    """
    def __init__(self,*args,**kwargs):
        super(ExplorationDoneState,self).__init__(*args,**kwargs)
        self.clear_middlewares()
        self.add_middleware(ResetMiddleware(state=self))
        self.add_middleware(MoveCommandMiddleware(state=self))

    def __str__(self):
        return "ee"

    def post_process(self,label,msg):
        type,msg = label,msg
        if (type in CMD_SOURCES and msg.get_msg()==PMessage.M_START_FASTRUN):
            # get the fast run commands
            self.transit_state(FastRunState)
            return self.get_commands_for_fastrun(),[]
        return [],[]

    def get_commands_for_fastrun(self):
        "return a list of command PMessage"
        algo = AStarShortestPathAlgo(map_ref=self._map_ref,target_pos=self._map_ref.get_end_zone_center_pos())
        cmd_list = algo.get_shortest_path(robot_pos=self._robot_ref.get_position(),robot_ori=self._robot_ref.get_orientation())
        return [PMessage(type=PMessage.T_COMMAND,msg=PMessage.M_START_FASTRUN)] + [PMessage(type=PMessage.T_COMMAND,msg=cmd) for cmd in cmd_list]


class FastRunState(BaseState):
    """
    only receive ack from robot
    """
    def __str__(self):
        return "run"

    def __init__(self,*args,**kwargs):
        super(FastRunState,self).__init__(*args,**kwargs)
        self.clear_middlewares()

    def post_process(self,label,msg):
        type,msg = label,msg
        if (type==ARDUINO_LABEL and msg.get_type()==PMessage.T_ROBOT_MOVE):
            # update internally
            self._robot_ref.execute_command(msg.get_msg())
            if (self._robot_ref.get_position()==self._map_ref.get_end_zone_center_pos()):
                self.transit_state(EndState)
            return [],[PMessage(type=PMessage.T_ROBOT_MOVE,msg=msg.get_msg())]
        else:
            return [],[]

class EndState(BaseState):
    """
    only accept reset command from android
    """
    def __init__(self,*args,**kwargs):
        super(EndState,self).__init__(*args,**kwargs)
        self.clear_middlewares()
        self.add_middleware(ResetMiddleware(state=self))
        self.add_middleware(MoveCommandMiddleware(state=self))

    def __str__(self):
        return "EndState"

    def post_process(self,label,msg):
        return [],[]