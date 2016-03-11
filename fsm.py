"""
module for implementing Finite State Machine
"""
import os
from abc import ABCMeta,abstractmethod
import time
from thread import start_new_thread
from common import *
from common.timer import Timer
from common.pmessage import PMessage
from common.amap import MapSetting
from algorithms.shortest_path import AStarShortestPathAlgo
from algorithms.maze_explore import MazeExploreAlgo

class StateMachine(object):
    """
    Interface specification for State Machine
    """
    _state = None # BaseState object

    def set_next_state(self,st):
        self._state = st

    def get_map_ref(self):
        raise NotImplementedError("get_map_ref not implemented")

    def get_robot_ref(self):
        raise NotImplementedError("get_robot_ref not implemented")

class BaseState(object):

    _machine = None
    _map_ref = None # MapRef object, obtained from machine
    _robot_ref = None # RobotRef object, obtained from machine

    def __init__(self,machine,**kwargs):
        self._machine = machine
        self._map_ref = self._machine.get_map_ref()
        self._robot_ref = self._machine.get_robot_ref()

    @abstractmethod
    def process_input(self,input_tuple):
        """
        :return: a list of command Message and a list of data Message
        can call machine.set_next_state() to trigger state transition
        """
        raise NotImplementedError()

class ReadyState(BaseState):
    def __str__(self):
        return "ReadyState"

    def process_input(self,input_tuple):
        "only listen for explore, fast run and move commands"
        type,msg = input_tuple

        # read android command
        if (msg.get_type()==PMessage.T_COMMAND):
            if (msg.get_msg()==PMessage.M_START_EXPLORE):
                # start exploration
                self._machine.set_next_state(ExplorationState(machine=self._machine))
                return [msg],[PMessage(type=PMessage.T_STATE_CHANGE,msg=msg.get_msg())]
            elif(msg.get_msg() in PMessage.M_MOVE_INSTRUCTIONS):
                # simple robot move
                self._machine.move_robot(msg.get_msg())
                return [msg],[PMessage(type=PMessage.T_ROBOT_MOVE,msg=msg.get_msg())]
            #TODO: remove this in production
            elif(msg.get_msg()==PMessage.M_END_EXPLORE):
                self._machine.set_next_state(ExplorationDoneState(machine=self._machine))
                print("jumped to exploration done state")
        elif(msg.get_type()==PMessage.T_SET_EXPLORE_TIME_LIMIT):
            try:
                limit = int(msg.get_msg())
                self._machine.set_exploration_time_limit(limit)
                return [],[]
            except:
                print("fail to set exploration time limit")
        elif(msg.get_type()==PMessage.T_SET_EXPLORE_COVERAGE):
            try:
                coverage = int(msg.get_msg())
                self._machine.set_exploration_coverage(coverage)
                return [],[]
            except:
                print("fail to set exploration coverage")
        #TODO: load map from file, for simulation only
        elif(msg.get_type()==PMessage.T_LOAD_MAP):
            path = msg.get_msg()
            self._machine.load_map_from_file(path)
            return [],[]
        elif(msg.get_type()==PMessage.T_SET_ROBOT_POS):
            x,y=msg.get_msg().split(",")
            self._machine.set_robot_pos((int(x),int(y)))
            # TODO: this is only for simulation
            return [PMessage(type=PMessage.T_SET_ROBOT_POS,msg=msg.get_msg())],[]
        elif(msg.get_type()==PMessage.T_SET_EXPLORE_SPEED):
            sec_per_step = float(msg.get_msg())
            self._machine.set_exploration_command_delay(sec_per_step)
            return [],[]
        elif(msg.get_type()==PMessage.T_MAP_UPDATE):
            return [],[msg]
        print("input {} is not valid".format(input_tuple))
        return [],[]


class ExplorationState(StateMachine,BaseState):
    """
    This state contains three substates: ExplorationFirstRound, ExplorationSecondRount, ExplorationThirdRound
    Will make change to RobotRef and MapRef
    """
    timer = None
    _time_limit = 0
    _cmd_buffer = []
    # for time limited exploration only
    LIST_LEN_BIAS = 2
    STEP_TIME_BIAS = 0.2
    MAP_UPDATE_IN_POS_LIST = False # map update sent in a list of clear positions and a list of obstacle positions
    SEND_COVERAGE_UPDATE = False

    # for debugging purpose
    map_trace_num = 1
    to_be_acked = []

    def __init__(self,machine,**kwargs):
        super(ExplorationState,self).__init__(machine,**kwargs)
        self.set_next_state(ExplorationFirstRoundState(machine=self))

    def get_map_ref(self):
        return self._machine.get_map_ref()

    def get_robot_ref(self):
        return self._machine.get_robot_ref()

    def __str__(self):
        return "explore"

    def process_input(self,input_tuple):
        type,msg = input_tuple
        # run timer if needed
        if (not self.timer and self._machine.get_exploration_time_limit()):
            self.setup_timer()
        # check coverage if needed
        current_coverage = 100 - self._map_ref.get_unknown_percentage()
        coverage_msg = PMessage(type=PMessage.T_CUR_EXPLORE_COVERAGE,msg=current_coverage) if self.SEND_COVERAGE_UPDATE else None
        # android "end explore" command
        if (type in CMD_SOURCES and msg.get_type()==PMessage.T_COMMAND and msg.get_msg()==PMessage.M_END_EXPLORE):
            self.end_exploration()
            return [PMessage(type=PMessage.T_COMMAND,msg=PMessage.M_END_EXPLORE)],\
                   [coverage_msg]
        elif(type in CMD_SOURCES and msg.get_type()==PMessage.T_SET_EXPLORE_SPEED):
            #TODO: change this deprecated method
            sec_per_step = float(msg.get_msg())
            self._machine.set_exploration_command_delay(sec_per_step)
            return [],[]

        # update from arduino
        if (type==ARDUINO_LABEL and msg.get_type()==PMessage.T_ROBOT_MOVE):
            if (self.to_be_acked and msg.get_msg()==self.to_be_acked[0]):
                self.to_be_acked = self.to_be_acked[1:]
                return [],[msg]

        if (type!=ARDUINO_LABEL or msg.get_type()!=PMessage.T_MAP_UPDATE):
            return [],[]
        # update internal map
        sensor_values = map(int,msg.get_msg().split(","))
        if (len(sensor_values)!=5):
            return [],[]
        clear_pos_list,obstacle_pos_list = self._machine.update_map(sensor_values)
        map_update_to_send = [clear_pos_list,obstacle_pos_list] if self.MAP_UPDATE_IN_POS_LIST else msg.get_msg().strip()
        # for debugging purpose
        map_str = get_map_trace(map_ref=self._map_ref,robot_ref=self._robot_ref)
        map_str = "\n\n-----------------# {}-------------------------\n\n{}".format(self.map_trace_num,map_str)
        self.map_trace_num +=1
        append_map_to_file(map_str)
        print("============================================================")
        print("Current robot position: {}".format(self._machine.get_robot_ref().get_position()))
        print("Current robot ori: {}".format(self._machine.get_robot_ref().get_orientation().get_value()))
        if (not self.is_going_back()):
            # check whether exploration is finished
            if (self.can_end_exploration()):
                print("Can end exploration (from explorationstate main)")
                if (self._robot_ref.get_position()!=self._map_ref.get_start_zone_center_pos()):
                    self.set_next_state(ExplorationGoBackState(machine=self))
                else:
                    self._map_ref.save_map_to_file("temp.bin")
                    self._machine.set_next_state(ExplorationDoneState(machine=self._machine))
                    return [PMessage(type=PMessage.T_COMMAND,msg=PMessage.M_END_EXPLORE)],\
                           [PMessage(type=PMessage.T_MAP_UPDATE,msg=map_update_to_send),coverage_msg]
            if (self.need_to_go_back()):
                self.set_next_state(ExplorationGoBackState(machine=self))

        cmd_list,data_list = self._state.process_input(input_tuple=input_tuple)
        data_list = [PMessage(type=PMessage.T_MAP_UPDATE,msg=map_update_to_send),coverage_msg] + data_list

        return cmd_list,data_list

    def setup_timer(self):
        self.timer = Timer(limit=self._machine.get_exploration_time_limit()
                           ,end_callback=self.time_up,interval_callback=self.time_tick)
        self.timer.start()

    def stop_timer(self):
        if (hasattr(self,"timer") and self.timer and self.timer.is_timing()):
            self.timer.shutdown()

    def time_up(self):
        "action when time for exploration is up"
        print("Time for exploration is up")
        self._machine.update_remaining_explore_time(0)
        #self._machine.set_next_state(ExplorationDoneState(machine=self._machine))

    def time_tick(self,time_remained):
        self._machine.update_remaining_explore_time(time_remained)

    def is_going_back(self):
        return self._state.__class__ == ExplorationGoBackState

    def can_end_exploration(self):
        "can end exploration when map is fully explored or time is up and robot is back at start point, or coverage limit is reached and robot is at start"
        #TODO: 60 is hardcoded
        self._map_ref.save_map_to_file("temp.bin")
        return self._map_ref.is_fully_explored() or\
            (self.timer and not self.timer.is_timing() and self._machine.is_robot_at_start()) or\
            (self._machine.get_exploration_coverage_limit() and self._machine.get_current_exploration_coverage()>=self._machine.get_exploration_coverage_limit() and self._machine.is_robot_at_start()) or\
            (self._map_ref.get_unknown_percentage()<60 and self._robot_ref.get_position()==self._map_ref.get_start_zone_center_pos())

    def add_robot_move_to_be_ack(self,move):
        self.to_be_acked.append(move)

    def end_exploration(self):
        self.stop_timer()
        self._machine.set_next_state(ExplorationDoneState(machine=self._machine))

    def need_to_go_back(self):
        "need to go back if half of the time limit has passed or coverage limit has reached"
        return (self.timer and self.timer.get_time_passed() >= (self._time_limit-3*self._machine.get_exploration_command_delay())/2.0 or
        self._machine.get_exploration_coverage_limit() and self._machine.get_current_exploration_coverage()>=self._machine.get_exploration_coverage_limit())


class ExplorationFirstRoundState(BaseState):
    """
    Substate of ExplorationState
    Explore along the wall,only return commands and robot move update
    will change robotRef
    """
    _explore_algo = None

    def __init__(self,machine,**kwargs):
        super(ExplorationFirstRoundState,self).__init__(machine=machine,**kwargs)
        self._explore_algo = MazeExploreAlgo(robot=self._machine.get_robot_ref(),map_ref=self._machine.get_map_ref())

    def process_input(self,input_tuple):
        # get next move
        command = self._explore_algo.get_next_move()
        self._robot_ref.execute_command(command)
        if(self._robot_ref.get_position()==self._map_ref.get_start_zone_center_pos() and self._map_ref.get_unknown_percentage()<50):
            self._machine.set_next_state(ExplorationSecondRoundState(machine=self._machine))
        self._machine.add_robot_move_to_be_ack(command)
        return [PMessage(type=PMessage.T_COMMAND,msg=command)],\
               []#[PMessage(type=PMessage.T_ROBOT_MOVE,msg=command)]

class ExplorationSecondRoundState(BaseState):
    """
    Substate of ExplorationState
    Explore whatever hasn't been explored
    will change robotRef
    """
    def process_input(self,input_tuple):
        #TODO: make the robot explore unexplored area
        self._machine.set_next_state(ExplorationGoBackState(machine=self._machine))
        return [],[]

class ExplorationGoBackState(BaseState):
    """
    Substate of ExplorationState
    for going back to start position
    machine must be ExplorationState object
    no change to robotRef and mapRef
    """
    _cmd_buffer = []
    started_go_back = False

    def process_input(self,input_tuple):
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
    def __str__(self):
        return "ee"

    def process_input(self,input_tuple):
        type,msg = input_tuple
        if (type in CMD_SOURCES and msg.get_msg()==PMessage.M_START_FASTRUN):
            # get the fast run commands
            self._machine.set_next_state(FastRunState(machine=self._machine))
            return self.get_commands_for_fastrun(),\
                   []

        elif (type in CMD_SOURCES and msg.get_msg()==PMessage.M_RESET):
            self._machine.reset()
            self._machine.set_next_state(ReadyState(machine=self._machine))
            return [PMessage(type=PMessage.T_COMMAND,msg=PMessage.M_RESET)],[]

        elif (type in CMD_SOURCES and msg.get_type()==PMessage.T_COMMAND and msg.get_msg() in PMessage.M_MOVE_INSTRUCTIONS):
            # simple robot move
            self._machine.move_robot(msg.get_msg())
            return [msg],[PMessage(type=PMessage.T_ROBOT_MOVE,msg=msg.get_msg())]

        else:
            return [],[]

    def get_commands_for_fastrun(self):
        "return a list of command PMessage"
        cmd_list = self._machine.get_fast_run_commands()
        return [PMessage(type=PMessage.T_COMMAND,msg=PMessage.M_START_FASTRUN)] + [PMessage(type=PMessage.T_COMMAND,msg=cmd) for cmd in cmd_list]


class FastRunState(BaseState):
    """
    only receive ack from robot
    """
    def __str__(self):
        return "run"

    def process_input(self,input_tuple):
        type,msg = input_tuple
        if (type==ARDUINO_LABEL and msg.get_type()==PMessage.T_ROBOT_MOVE):
            # update internally
            self._machine.move_robot(msg.get_msg())
            if (self._machine.is_robot_at_destination()):
                self._machine.set_next_state(EndState(machine=self._machine))
                return [],[PMessage(type=PMessage.T_ROBOT_MOVE,msg=msg.get_msg())]
            else:
                return [],[PMessage(type=PMessage.T_ROBOT_MOVE,msg=msg.get_msg())]
        else:
            return [],[]

class EndState(BaseState):
    """
    only accept reset command from android
    """
    def __str__(self):
        return "EndState"

    def process_input(self,input_tuple):
        type,msg = input_tuple
        if (type in CMD_SOURCES and msg.get_msg()==PMessage.M_RESET):
            self._machine.reset()
            self._machine.set_next_state(ReadyState(machine=self._machine))
            return [PMessage(type=PMessage.T_COMMAND,msg=PMessage.M_RESET)],[]
        elif (type in CMD_SOURCES and msg.get_type()==PMessage.T_COMMAND):
            # self._robot_ref.execute_command(msg.get_msg())
            return [PMessage(type=PMessage.T_COMMAND,msg=msg.get_msg())],[]
        else:
            return [],[]

# for debugging purpose only
def get_map_trace(map_ref,robot_ref):
    map_str = ""
    cell_format = "{}|"
    for y in range(map_ref.size_y):
        for x in range(map_ref.size_x):
            if ((x,y) in robot_ref.get_occupied_postions()):
                if ((x,y)==robot_ref.get_head_position()):
                    map_str += cell_format.format("H")
                else:
                    map_str += cell_format.format("B")
            else:
                if (map_ref.get_cell(x,y)==MapSetting.OBSTACLE):
                    map_str += cell_format.format("X")
                elif (map_ref.get_cell(x,y)==MapSetting.CLEAR):
                    map_str += cell_format.format(" ")
                else:# unknown
                    map_str += cell_format.format("?")
        map_str += "\n"
    return map_str

def append_map_to_file(map_str):
    file_name = "map_trace.txt"
    # create the file if not exists
    if not os.path.exists(file_name):
        f = open(file_name,"w")
        f.close()

    # append map to it
    with open(file_name,"a") as f:
        f.write(map_str)