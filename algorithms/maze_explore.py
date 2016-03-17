from common import *
from common.amap import MapRef
from common.pmessage import PMessage
from common.debug import debug,DEBUG_ALGO
import random

class MazeExploreAlgo():
    _robot = None # reference to robot object
    _map_ref = None # reference to map array
    _history_ls = None # list of position, orientation tuples
    _CHECK_HISTORY_FOR_LOOP = False

    CAN_ACCESS,CANNOT_ACCESS,UNSURE = 1,2,3
    # in the exploration, the robot will attempt the following action in sequence
    DEFAULT_ACTION_PRECEDENCE = [PMessage.M_TURN_RIGHT,PMessage.M_MOVE_FORWARD,PMessage.M_TURN_LEFT]
    PRECEDENCE_UPDATE_DICT = {
        PMessage.M_TURN_RIGHT:{CAN_ACCESS:[PMessage.M_MOVE_FORWARD,PMessage.M_TURN_LEFT,PMessage.M_TURN_RIGHT],UNSURE:[PMessage.M_MOVE_FORWARD,PMessage.M_TURN_LEFT,PMessage.M_TURN_RIGHT]},
        PMessage.M_MOVE_FORWARD:{CAN_ACCESS:DEFAULT_ACTION_PRECEDENCE,UNSURE:DEFAULT_ACTION_PRECEDENCE}, # front got three sensors, so no unsure
        PMessage.M_TURN_LEFT : {CAN_ACCESS:[PMessage.M_MOVE_FORWARD,PMessage.M_TURN_LEFT,PMessage.M_TURN_RIGHT],UNSURE:[PMessage.M_MOVE_FORWARD,PMessage.M_TURN_LEFT,PMessage.M_TURN_RIGHT]}
    }
    action_precedence = DEFAULT_ACTION_PRECEDENCE

    MOVE_ALONG_WALL_STRATEGY = "alongwall"
    NO_DUPLICATE_EXPLORE_STRATEGY = "noduplicate"

    _strategy = MOVE_ALONG_WALL_STRATEGY

    def __init__(self,robot,map_ref):
        self._robot = robot
        self._map_ref = map_ref
        self._history_ls = []

    def get_next_move(self):
        "return the command to be executed next"
        if (self._strategy == self.MOVE_ALONG_WALL_STRATEGY):
            return self.move_along_wall()
        else:
            return self.move_along_wall_efficient()

    def move_along_wall_efficient(self):
        "under dev"
        #TODO: change this code and test
        if ((self._robot.get_position(),self._robot.get_orientation()) in self._history_ls):
            debug("Loop detected, go back",DEBUG_ALGO)
            self.action_precedence = [PMessage.M_TURN_RIGHT,PMessage.M_MOVE_FORWARD,PMessage.M_TURN_LEFT]
            return PMessage.M_TURN_BACK
        else:
            debug("History: pos({}), orientation({})".format(self._robot.get_position(),self._robot.get_orientation()),DEBUG_ALGO)
            self._history_ls.append((self._robot.get_position(),self._robot.get_orientation()))

        candidate_actions = [] # list of (action,utility)
        for action in self.action_precedence:
            ori = self.get_ori_to_check(desired_action=action)
            status = self.check_status(ori)
            if (status!=self.CANNOT_ACCESS):
                utility = self._robot.get_action_utility_points(action=action,map_ref=self._map_ref)
                if (not candidate_actions):
                    candidate_actions.append((action,utility))
                else:
                    if (utility==candidate_actions[0][1]):
                        candidate_actions.append((action,utility))
                    elif (utility>candidate_actions[0][1]):
                        candidate_actions = [(action,utility)]

        if (candidate_actions):#pick the action with highest utility
            return candidate_actions[random.randint(0,len(candidate_actions)-1)][0]
        else:# if no action can be done, then try going back
            return PMessage.M_TURN_BACK

    def move_along_wall(self):
        # check whether the robot has gone into a cycle
        if (self._CHECK_HISTORY_FOR_LOOP):
            if ((self._robot.get_position(),self._robot.get_orientation()) in self._history_ls):
                self.action_precedence = [PMessage.M_TURN_RIGHT,PMessage.M_MOVE_FORWARD,PMessage.M_TURN_LEFT]
                debug("Loop detected, go back",DEBUG_ALGO)
                self._history_ls = []
                return PMessage.M_TURN_BACK
            else:
                debug("History: pos({}), orientation({})".format(self._robot.get_position(),self._robot.get_orientation()),DEBUG_ALGO)
                self._history_ls.append((self._robot.get_position(),self._robot.get_orientation()))

        for action in self.action_precedence:
            ori = self.get_ori_to_check(desired_action=action)
            status = self.check_status(ori)
            if (status!=self.CANNOT_ACCESS):
                self.action_precedence = self.PRECEDENCE_UPDATE_DICT[action][status]
                return action

        return PMessage.M_TURN_BACK

    def check_status(self,ori):
        "return CAN_ACCESS,CANNOT_ACCESS or UNSURE"
        # locate the three blocks to check
        pos_change = ori.to_pos_change()
        side_pos_delta = [(pos_change[0]*2,i) for i in range(-1,2)] if pos_change[1] == 0\
                            else [(i,pos_change[1]*2) for i in range(-1,2)] # position difference from the target blocks to center
        # check the blocks
        has_unexplored = False
        robot_centre_pos = self._robot.get_position()
        for delta in side_pos_delta:
            target_pos = (delta[0]+robot_centre_pos[0],delta[1]+robot_centre_pos[1])
            x,y = target_pos[0], target_pos[1]
            if (self._map_ref.is_out_of_arena(x,y)):
                return self.CANNOT_ACCESS
            if (self._map_ref.get_cell(x,y)==MapRef.OBSTACLE):
                return self.CANNOT_ACCESS
            elif (self._map_ref.get_cell(x,y)==MapRef.UNKNOWN):
                has_unexplored = True
        return self.UNSURE if has_unexplored else self.CAN_ACCESS


    def get_ori_to_check(self,desired_action):
        "return the orientation after executing given a potential action"
        return (self._robot.get_orientation().if_applied_action(desired_action))