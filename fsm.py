"""
module for implementing Finite State Machine
"""
from abc import ABCMeta,abstractmethod
import time
from thread import start_new_thread
from common import *
from common.timer import Timer
from common.pmessage import PMessage

class StateMachine():
    """
    Interface specification for State Machine
    """
    @abstractmethod
    def set_next_state(self,state_name):
        raise NotImplementedError()
    @abstractmethod
    def move_robot(self,action):
        raise NotImplementedError()
    @abstractmethod
    def update_map(self,sensor_values):
        raise NotImplementedError()
    @abstractmethod
    def get_next_exploration_move(self):
        raise NotImplementedError()
    @abstractmethod
    def is_map_fully_explored(self):
        raise NotImplementedError()
    @abstractmethod
    def get_fast_run_commands(self):
        raise NotImplementedError()
    @abstractmethod
    def is_robot_at_destination(self):
        raise NotImplementedError()
    @abstractmethod
    def reset(self):
        raise NotImplementedError()
    @abstractmethod
    def set_exploration_time_limit(self,time_limit):
        raise NotImplementedError()
    @abstractmethod
    def set_exploration_coverage(self,coverage_percent):
        raise  NotImplementedError()

class BaseState():

    _machine = None

    def __init__(self,machine,**kwargs):
        self._machine = machine

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
        if (type!=ANDROID_LABEL):
            return [],[]
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
        print("input {} is not valid".format(input_tuple))
        return [],[]


class ExplorationState(BaseState):
    """
    only accept sensor readings from arduino
    """
    timer = None

    def __str__(self):
        return "ExplorationState"

    def process_input(self,input_tuple):
        type,msg = input_tuple
        # run timer if needed
        if (not self.timer):
            time_limit = self._machine.get_exploration_time_limit()
            if (time_limit):
                self.timer = Timer(limit=time_limit,end_callback=self.time_up,interval_callback=self.time_tick)
                self.timer.start()
        # check coverage if needed
        coverage_limit = self._machine.get_exploration_coverage_limit()
        current_coverage = self._machine.get_current_exploration_coverage()
        coverage_msg = PMessage(type=PMessage.T_CUR_EXPLORE_COVERAGE,msg=current_coverage)
        # android "end explore" command
        if (type==ANDROID_LABEL and msg.get_type()==PMessage.T_COMMAND and msg.get_msg()==PMessage.M_END_EXPLORE):
            # stop timer and transit state
            if (hasattr(self,"timer") and self.timer and self.timer.is_timing()):
                self.timer.shutdown()
            self._machine.set_next_state(ExplorationDoneState(machine=self._machine))
            return [PMessage(type=PMessage.T_COMMAND,msg=PMessage.M_END_EXPLORE)],\
                   [coverage_msg]
        # update from arduino
        if (type!=ARDUINO_LABEL):
            return [],[]
        # update internal map
        sensor_values = map(int,msg.get_msg().split(","))
        self._machine.update_map(sensor_values)
        # check whether exploration is finished
        if (self._machine.is_map_fully_explored()):
            self._machine.set_next_state(ExplorationDoneState(machine=self._machine))
            return [PMessage(type=PMessage.T_COMMAND,msg=PMessage.M_END_EXPLORE)],\
                   [PMessage(type=PMessage.T_MAP_UPDATE,msg=msg.get_msg()),coverage_msg]

        if (coverage_limit and current_coverage>=coverage_limit):
            # already reach coverage limit, terminate exploration
            self._machine.set_next_state(ExplorationDoneState(machine=self._machine))
            return [PMessage(type=PMessage.T_COMMAND,msg=PMessage.M_END_EXPLORE)],\
                    [PMessage(type=PMessage.T_MAP_UPDATE,msg=msg.get_msg()),coverage_msg]
        else:
            # get next move
            command = self._machine.get_next_exploration_move()
            # command delay
            time.sleep(self._machine.get_exploration_command_delay())
            self._machine.move_robot(command)
            return [PMessage(type=PMessage.T_COMMAND,msg=command)],\
                   [PMessage(type=PMessage.T_MAP_UPDATE,msg=msg.get_msg()),PMessage(type=PMessage.T_ROBOT_MOVE,msg=command),coverage_msg]

    def time_up(self):
        "action when time for exploration is up"
        print("Time for exploration is up")
        self._machine.update_remaining_explore_time(0)
        self._machine.set_next_state(ExplorationDoneState(machine=self._machine))

    def time_tick(self,time_remained):
        self._machine.update_remaining_explore_time(time_remained)


class ExplorationDoneState(BaseState):
    """
    only accept start fast run command from android
    """
    def __str__(self):
        return "ExplorationDoneState"

    def process_input(self,input_tuple):
        type,msg = input_tuple
        if (type ==ANDROID_LABEL and msg.get_msg()==PMessage.M_START_FASTRUN):
            # get the fast run commands
            cmd_list = self._machine.get_fast_run_commands()
            self._machine.set_next_state(FastRunState(machine=self._machine))
            reply_commands = [PMessage(type=PMessage.T_COMMAND,msg=PMessage.M_START_FASTRUN)]
            reply_commands.extend([PMessage(type=PMessage.T_COMMAND,msg=cmd) for cmd in cmd_list])
            return reply_commands,\
                   [PMessage(type=PMessage.T_STATE_CHANGE,msg=msg.get_msg())]

        elif (type==ANDROID_LABEL and msg.get_msg()==PMessage.M_RESET):
            self._machine.reset()
            self._machine.set_next_state(ReadyState(machine=self._machine))
            return [PMessage(type=PMessage.T_COMMAND,msg=PMessage.M_RESET)],[PMessage(type=PMessage.T_STATE_CHANGE,msg=PMessage.M_RESET)]
        elif (type==ANDROID_LABEL and msg.get_type()==PMessage.T_COMMAND and msg.get_msg() in PMessage.M_MOVE_INSTRUCTIONS):
            # simple robot move
            self._machine.move_robot(msg.get_msg())
            return [msg],[PMessage(type=PMessage.T_ROBOT_MOVE,msg=msg.get_msg())]
        else:
            return [],[]


class FastRunState(BaseState):
    """
    only receive ack from robot
    """
    def __str__(self):
        return "FastRunState"

    def process_input(self,input_tuple):
        type,msg = input_tuple
        if (type==ARDUINO_LABEL and msg.get_type()==PMessage.T_ROBOT_MOVE):
            # update internally
            self._machine.move_robot(msg.get_msg())
            if (self._machine.is_robot_at_destination()):
                self._machine.set_next_state(EndState(machine=self._machine))
                return [],[PMessage(type=PMessage.T_ROBOT_MOVE,msg=msg.get_msg()),PMessage(type=PMessage.T_STATE_CHANGE,msg=PMessage.M_REACH_END)]
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
        if (type==ANDROID_LABEL and msg.get_msg()==PMessage.M_RESET):
            self._machine.reset()
            self._machine.set_next_state(ReadyState(machine=self._machine))
            return [PMessage(type=PMessage.T_COMMAND,msg=PMessage.M_RESET)],[PMessage(type=PMessage.T_STATE_CHANGE,msg=PMessage.M_RESET)]
        else:
            return [],[]