"""
module for implementing Finite State Machine
"""
from abc import ABCMeta,abstractmethod
from common import *
from common import pmessage
from common.pmessage import PMessage

class StateMachine():
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
            elif(msg.get_msg()==PMessage.M_JUMP_EXPLORE):
                self._machine.load_map_from_file("D:/map.txt")
                self._machine.set_next_state(ExplorationDoneState(machine=self._machine))
                print("loaded map from file")
        print("input {} is not valid".format(input_tuple))
        return [],[]


class ExplorationState(BaseState):
    """
    only accept sensor readings from arduino
    """
    def __str__(self):
        return "ExplorationState"

    def process_input(self,input_tuple):
        type,msg = input_tuple
        if (type!=ARDUINO_LABEL):
            return [],[]
        # update internal map
        sensor_values = map(int,msg.get_msg().split(","))
        self._machine.update_map(sensor_values)
        # check whether exploration is finished
        if (self._machine.is_map_fully_explored()):
            self._machine.set_next_state(ExplorationDoneState(machine=self._machine))
            return [PMessage(type=PMessage.T_COMMAND,msg=PMessage.M_END_EXPLORE)],[PMessage(type=PMessage.T_MAP_UPDATE,msg=msg.get_msg())]
        # get next move
        command = self._machine.get_next_exploration_move()
        self._machine.move_robot(command)
        return [PMessage(type=PMessage.T_COMMAND,msg=command)],\
               [PMessage(type=PMessage.T_MAP_UPDATE,msg=msg.get_msg()),PMessage(type=PMessage.T_ROBOT_MOVE,msg=command)]


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
        else:
            return [],[]