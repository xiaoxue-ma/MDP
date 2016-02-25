from common import *
from common.amap import MapRef
from common.pmessage import PMessage


class MazeExploreAlgo():
    _robot = None  # reference to robot object
    _map_ref = None  # reference to map array

    CAN_ACCESS, CANNOT_ACCESS, UNSURE = 1, 2, 3
    # in the exploration, the robot will attempt the following action in sequence
    DEFAULT_ACTION_PRECEDENCE = [PMessage.M_TURN_RIGHT, PMessage.M_MOVE_FORWARD, PMessage.M_TURN_LEFT]
    PRECEDENCE_UPDATE_DICT = {
        PMessage.M_TURN_RIGHT: {CAN_ACCESS: [PMessage.M_MOVE_FORWARD, PMessage.M_TURN_LEFT],
                                UNSURE: [PMessage.M_MOVE_FORWARD, PMessage.M_TURN_LEFT]},
        PMessage.M_MOVE_FORWARD: {CAN_ACCESS: DEFAULT_ACTION_PRECEDENCE},  # front got three sensors, so no unsure
        PMessage.M_TURN_LEFT: {CAN_ACCESS: DEFAULT_ACTION_PRECEDENCE, UNSURE: DEFAULT_ACTION_PRECEDENCE}
    }
    action_precedence = DEFAULT_ACTION_PRECEDENCE

    def __init__(self, robot, map_ref):
        self._robot = robot
        self._map_ref = map_ref

    def get_next_move(self):
        "return the command to be executed next"
        for action in self.action_precedence:
            ori = self.get_ori_to_check(desired_action=action)
            status = self.check_status(ori)
            if status != self.CANNOT_ACCESS:
                # update the action precedence
                self.action_precedence = self.PRECEDENCE_UPDATE_DICT[action][status]
                # do this action
                return action

    def check_status(self, ori):
        """return CAN_ACCESS,CANNOT_ACCESS or UNSURE"""
        # locate the three blocks to check
        pos_change = ori.to_pos_change()
        side_pos_delta = [(pos_change[0] * 2, i) for i in range(-1, 2)] if pos_change[1] == 0 \
            else [(i, pos_change[1] * 2) for i in range(-1, 2)]  # position difference from the target blocks to center
        # check the blocks
        has_unexplored = False
        robot_centre_pos = self._robot.get_position()
        for delta in side_pos_delta:
            target_pos = (delta[0] + robot_centre_pos[0], delta[1] + robot_centre_pos[1])
            x, y = target_pos[0], target_pos[1]
            if self._map_ref.is_out_of_arena(x, y):
                return self.CANNOT_ACCESS
            if self._map_ref.get_cell(x, y) == MapRef.OBSTACLE:
                return self.CANNOT_ACCESS
            elif self._map_ref.get_cell(x, y) == MapRef.UNKNOWN:
                has_unexplored = True
        return self.UNSURE if has_unexplored else self.CAN_ACCESS

    def get_ori_to_check(self, desired_action):
        """return the orientation after executing given a potential action"""
        return self._robot.get_orientation().if_applied_action(desired_action)