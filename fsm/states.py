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
from common.debug import debug, DEBUG_STATES
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
        except Exception as e:
            debug("Post process error: {}".format(e),DEBUG_STATES)
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

    _MAX_POSSIBLE_OBSTACLES = -1 # -1 means ignore

    def __init__(self,*args,**kwargs):
        super(ExplorationState,self).__init__(*args,**kwargs)
        self._map_ref = self._machine.get_map_ref()
        self._robot_ref = self._machine.get_robot_ref()
        self.clear_middlewares()
        self._mapupdate_mid = MapUpdateMiddlewareUsingMapBuffer(state=self)
        self.add_middleware(self._mapupdate_mid)
        self.set_next_state(ExplorationStateWithTimerAndCallibration(machine=self))

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
        # if (self._MAX_POSSIBLE_OBSTACLES!=-1 and self._map_ref.get_num_obstacles()>=self._MAX_POSSIBLE_OBSTACLES):
        #     self._map_ref.set_unknowns_as_clear()
        self._map_ref.save_map_to_file("temp.bin")
        self._machine.send_command(PMessage.M_END_EXPLORE)
        self._machine.set_next_state(ExplorationDoneState(machine=self._machine))

    def send_command(self,msg):
        self._machine.send_command(msg)

class ExplorationFirstRoundState(BaseState):
    """
    Substate of ExplorationState
    Explore along the wall,only return commands and robot move update
    will change robotRef
    """
    _explore_algo = None
    _end_coverage_threshold = 60 #TODO: this is hardcoded
    _USE_ROBOT_STATUS_UPDATE = True
    _explore_end = False

    def __init__(self,*args,**kwargs):
        super(ExplorationFirstRoundState,self).__init__(*args,**kwargs)
        self._explore_algo = MazeExploreAlgo(robot=self._machine.get_robot_ref(),map_ref=self._machine.get_map_ref())
        self._explore_end = False

    def post_process(self,label,msg):
        # get next move
        if (label==ARDUINO_LABEL and msg.is_map_update() and (not self._explore_end)):
            command = self._explore_algo.get_next_move()
            self.add_robot_move_to_be_ack(command)
            return [PMessage(type=PMessage.T_COMMAND,msg=command)],\
                   []
        else:
            return [],[]

    def add_robot_move_to_be_ack(self,move):
        self.add_expected_ack(label=ARDUINO_LABEL,msg=PMessage(type=PMessage.T_ROBOT_MOVE,msg=move),call_back=self.ack_move_to_android,args=[move])

    def ack_move_to_android(self,move):
        self._robot_ref.execute_command(move)
        self._map_ref.set_fixed_cells(self._robot_ref.get_occupied_postions(),MapSetting.CLEAR)
        debug("Current robot position:{}".format(self._robot_ref.get_position()),DEBUG_STATES)
        debug("Current map coverage: {}".format(100-self._map_ref.get_unknown_percentage()),DEBUG_STATES)
        if(self._robot_ref.get_position()==self._map_ref.get_start_zone_center_pos() and 100-self._map_ref.get_unknown_percentage()>self._end_coverage_threshold):
            debug("Ending Exploration",DEBUG_STATES)
            self.trigger_end_exploration()

        if (self._USE_ROBOT_STATUS_UPDATE):
            data_ls = [PMessage(type=PMessage.T_UPDATE_ROBOT_STATUS,msg="{},{},{}".format(
            self._robot_ref.get_position()[0],
            self._robot_ref.get_position()[1],
            self._robot_ref.get_orientation().get_value()
        ))]
        else:
            data_ls = [PMessage(type=PMessage.T_ROBOT_MOVE,msg=move)]

        return [],data_ls

    def trigger_end_exploration(self):
        self._explore_end = True
        self._machine.end_exploration()

class ExplorationFirstRoundStateWithTimer(ExplorationFirstRoundState):
    _timer = None # timer for sending extra command in case map update not sent back in time
    _MAP_UPDATE_TIME_LIMIT = 1E6

    def __init__(self,*args,**kwargs):
        super(ExplorationFirstRoundStateWithTimer,self).__init__(*args,**kwargs)
        self._timer = Timer(limit=self._MAP_UPDATE_TIME_LIMIT,end_callback=self.ask_for_map_update)
        #self._machine.add_mapupdate_listener(self._timer)

    def post_process(self,label,msg):
        cmd_ls,data_ls = super(ExplorationFirstRoundStateWithTimer,self).post_process(label,msg)
        if (cmd_ls):
            # get new command, stop the previous timer and start a new timer
            self._timer.shutdown()
            debug("Get new command, try to start timer",DEBUG_STATES)
            self._timer.start()
        return cmd_ls,data_ls

    def ask_for_map_update(self):
        self._machine.send_command(PMessage.M_GET_SENSOR)

    def trigger_end_exploration(self):
        self._timer.shutdown()
        super(ExplorationFirstRoundStateWithTimer,self).trigger_end_exploration()

class ExplorationStateWithTimerAndCallibration(ExplorationFirstRoundStateWithTimer):
    """
    wrapper class that sends additional Callibration message upon ack of robot move
    """
    _DO_ROBOT_POS_CORRECTION = False
    _SEND_CALLIBRATION_CMD = False

    def ack_move_to_android(self,move):
        cmd_ls,data_ls = super(ExplorationStateWithTimerAndCallibration,self).ack_move_to_android(move)
        # detect whether the robot is at a corner, send callibrate command if so
        blocked_sides = self._robot_ref.get_sides_fully_blocked(self._map_ref)
        shift_right = self.correct_robot_position(blocked_sides)
        # if (shift_right):
        #     data_msgs_to_send = [PMessage(type=PMessage.T_ROBOT_MOVE,msg=PMessage.M_SHIFT_RIGHT)]
        # else:
        #     data_msgs_to_send = []
        # currently let arduino callibrate right itself
        if (self._SEND_CALLIBRATION_CMD and
                (len(blocked_sides)>1 or len(blocked_sides)==1 and blocked_sides[0]==RIGHT)):
            callibration_msgs_to_send = self.get_callibration_msgs(blocked_sides)
        else:
            callibration_msgs_to_send=[]
        self._map_ref.set_fixed_cells(self._robot_ref.get_occupied_postions(),MapSetting.CLEAR)
        return callibration_msgs_to_send+cmd_ls,data_ls

    #TODO: this is the callibration logic
    def get_callibration_msgs(self,sides):
        "return a list of PMessage"
        if (len(sides)==1 and sides[0]==RIGHT and self._robot_ref.has_continuous_straight_moves(3)):
            # if right side fully blocked, send callibration if there's at least 3 straight moves
            debug("more than 3 straight moves in a row",DEBUG_STATES)
            self._robot_ref.clear_history()
            return [PMessage(type=PMessage.T_CALLIBRATE,msg=PMessage.M_CALLIBRATE_RIGHT)]
        elif(len(sides)==1 and sides[0]==FRONT):
            # if front side fully blocked, callibrate
            return [PMessage(type=PMessage.T_CALLIBRATE,msg=PMessage.M_CALLIBRATE_FRONT)]
        elif (len(sides)>1):
            # if at corner, callibrate
            ORI_TO_MSG = {
                FRONT:PMessage.M_CALLIBRATE_FRONT,
                LEFT:PMessage.M_CALLIBRATE_LEFT,
                RIGHT: PMessage.M_CALLIBRATE_RIGHT
            }
            return [PMessage(type=PMessage.T_CALLIBRATE,msg=ORI_TO_MSG[s]) for s in sides]
        else:
            return [],[]

    def correct_robot_position(self,block_sides):
        "move robot to the wall if >=3 obstacles detected along wall, return True if robot is shifted right"
        if (not self._DO_ROBOT_POS_CORRECTION):
            return False
        if RIGHT in block_sides:
            delta_x,delta_y = RIGHT.to_pos_change(self._robot_ref.get_orientation())
            x,y = sum_coordinate(self._robot_ref.get_position(),(delta_x*2,delta_y*2))
            if (self._map_ref.is_along_wall(x,y)):
                self._robot_ref.shift_right()
                self._map_ref.set_fixed_cells(self._robot_ref.get_occupied_postions(),MapSetting.CLEAR)
                return True

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
            self.transit_state(FastRunStateUsingExploration)
            return [PMessage(type=PMessage.T_COMMAND,msg=PMessage.M_START_FASTRUN)],[]
        return [],[]


class FastRunState(BaseState):
    """
    only receive ack from robot
    `cmd_buffer` : a list of commands to be sent
    `started`: boolean
    """
    _USE_ROBOT_STATUS_UPDATE = True

    def __str__(self):
        return "run"

    def __init__(self,*args,**kwargs):
        super(FastRunState,self).__init__(*args,**kwargs)
        self.started = False
        self.cmd_buffer = []
        self.add_expected_ack(label=ARDUINO_LABEL,msg=PMessage(type=PMessage.T_ROBOT_MOVE,msg=PMessage.M_START_FASTRUN),call_back=self.set_start)

    def set_start(self):
        self.started = True
        self.cmd_buffer = self.get_commands_for_fastrun()
        move = self.cmd_buffer[0]
        self.cmd_buffer = self.cmd_buffer[1:]
        self._machine.send_command(move)
        self.add_expected_ack(label=ARDUINO_LABEL,msg=PMessage(type=PMessage.T_ROBOT_MOVE,msg=move),call_back=self.continue_sending_command,args=[move])

    def continue_sending_command(self,move):
        # receive ack
        self._robot_ref.execute_command(move)
        # update android
        self.send_robot_update(move)
        # if still have commands, send
        if (self.cmd_buffer):
            new_move = self.cmd_buffer[0]
            self.cmd_buffer = self.cmd_buffer[1:]
            self._machine.send_command(new_move)
            self.add_expected_ack(label=ARDUINO_LABEL,msg=PMessage(type=PMessage.T_ROBOT_MOVE,msg=new_move),call_back=self.continue_sending_command,args=[new_move])
        else:# end of fast run
            self.transit_state(EndState(machine=self._machine))

    def send_robot_update(self,move):
        if (self._USE_ROBOT_STATUS_UPDATE):
            msg = PMessage(type=PMessage.T_UPDATE_ROBOT_STATUS,msg="{},{},{}".format(
            self._robot_ref.get_position()[0],
            self._robot_ref.get_position()[1],
            self._robot_ref.get_orientation().get_value()
        ))
        else:
            msg = [PMessage(type=PMessage.T_ROBOT_MOVE,msg=move)]
        self._machine.send_data_pmsg(msg)

    def get_commands_for_fastrun(self):
        "return a list of command PMessage"
        algo = AStarShortestPathAlgo(map_ref=self._map_ref,target_pos=self._map_ref.get_end_zone_center_pos())
        cmd_list = algo.get_shortest_path(robot_pos=self._robot_ref.get_position(),robot_ori=self._robot_ref.get_orientation())
        return cmd_list

    def post_process(self,label,msg):
        return [],[]

class FastRunStateUsingExploration(FastRunState):
    """
    Use exploration strategy to run fast run
    `_explore_algo`: ExplorationAlgo object
    """

    def set_start(self):
        self.started = True
        # if the robot is not in correct orientation (cannot face WEST), correct it
        if (self._robot_ref.get_orientation()==WEST):
            correction_command = PMessage.M_TURN_LEFT
            self._machine.send_command(correction_command)
            self.add_expected_ack(label=ARDUINO_LABEL,msg=PMessage(type=PMessage.T_ROBOT_MOVE,msg=correction_command),call_back=self.continue_sending_command,args=[correction_command])
        else:
            self.continue_sending_command()

    def continue_sending_command(self,move=None):
        if (hasattr(self,"_explore_algo") and move):
            # receive ack
            self._robot_ref.execute_command(move)
            # update android
            self.send_robot_update(move)
            # if still have commands, send
            if (self._robot_ref.get_position()!=self._map_ref.get_end_zone_center_pos()):
                new_move = self._explore_algo.get_next_move()
                self._machine.send_command(new_move)
                self.add_expected_ack(label=ARDUINO_LABEL,msg=PMessage(type=PMessage.T_ROBOT_MOVE,msg=new_move),call_back=self.continue_sending_command,args=[new_move])
            else:# end of fast run
                self.transit_state(EndState(machine=self._machine))
        else:
            # init algo
            self._explore_algo = MazeExploreAlgo(robot=self._robot_ref,map_ref=self._map_ref)
            new_move = self._explore_algo.get_next_move()
            self._machine.send_command(new_move)
            self.add_expected_ack(label=ARDUINO_LABEL,msg=PMessage(type=PMessage.T_ROBOT_MOVE,msg=new_move),call_back=self.continue_sending_command,args=[new_move])

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