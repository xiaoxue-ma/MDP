from common.constants import *
from common.pmessage import PMessage

class Orientation():
    _val = 0

    def __init__(self,val):
        self._val = val

    def get_value(self):
        return self._val

    def get_name(self):
        raise NotImplementedError()

class AbsoluteOrientation(Orientation):
    """
    internally, absolute orientation is represented as eight numbers as follows
    0  1      2
    7 center  3  ^up
    6  5      4
    """
    POS_CHANGE_DICT = {0:(-1,-1),1:(0,-1),2:(1,-1),3:(1,0),4:(1,1),5:(0,1),6:(-1,1),7:(-1,0)}
    ACTION_TO_ORI_CHANGE = {PMessage.M_TURN_LEFT:-2,PMessage.M_TURN_RIGHT:2,PMessage.M_MOVE_FORWARD:0}
    ORI_VERBOSE = {1:'up',5:'down',7:'left',3:'right'}

    def to_pos_change(self):
        "return tuple representing the position change relative to the center"
        return self.POS_CHANGE_DICT[self._val]

    def if_applied_action(self,action):
        "return the resulting ori if action applied"
        new_val = (self._val + self.ACTION_TO_ORI_CHANGE[action])%8
        return AbsoluteOrientation(new_val)

    def get_minimum_turns_to(self,a_ori):
        "return number of turns needed to be made to reach a_ori"
        val_diff = (a_ori._val-self._val)%8
        val_diff = min(val_diff,8-val_diff)
        return int(val_diff/2)

    def to_left(self):
        return AbsoluteOrientation((self._val+2*3)%8)

    def to_right(self):
        return AbsoluteOrientation((self._val+2*1)%8)

    def to_back(self):
        return AbsoluteOrientation((self._val+2*2)%8)

    @staticmethod
    def get_ori_at_dest(start_pos,dest_pos):
        "return the resulting ori if the robot go from start to dest"
        pos_diff = (dest_pos[0]-start_pos[0],dest_pos[1]-start_pos[1])
        LOOPUP_DICT = {(0,-1):1,(1,0):3,(0,1):5,(-1,0):7}
        new_val = LOOPUP_DICT[pos_diff]
        return AbsoluteOrientation(new_val)

    @staticmethod
    def get_turn_actions(start_ori,end_ori):
        "return the list of actions to turn from start_ori to end_ori, None if no action needed"
        if (end_ori.get_value()==(start_ori.get_value()+2)%8):
            return [PMessage.M_TURN_RIGHT]
        elif(end_ori.get_value()==(start_ori.get_value()-2)%8):
            return [PMessage.M_TURN_LEFT]
        elif (end_ori.get_value()==(start_ori.get_value()+4)%8):
            # turn 180 degrees
            return [PMessage.M_TURN_RIGHT,PMessage.M_TURN_RIGHT]
        else: # no need to turn
            return []

    def get_name(self):
        "get verbose name"
        return self.ORI_VERBOSE[self._val]

class RelativeOrientation(Orientation):
    """
    internally, relative orientation is represented as eight numbers as follows
    -1  0      1
    -2  center 2  ^front
    -3  4      3
    """

    ORI_VERBOSE = {-1:'front-left',0:'front',1:'front-right',-2:'left',2:'right',-3:'back-left',3:'back-right',4:'back'}

    def get_actual_abs_ori(self,ref_front_ori,front_major=True):
        "return absolute orientation, if front_major is True, front-left and front-right will be considered as front"
        val = self._val
        if (front_major and abs(val)==1): val = 0
        abs_val = (val + ref_front_ori.get_value())%8
        return AbsoluteOrientation(abs_val)

    def to_pos_change(self,rel_front_ori):
        abs_val = (self._val + rel_front_ori.get_value())%8
        return AbsoluteOrientation(abs_val).to_pos_change()

    def __unicode__(self):
        return self.ORI_VERBOSE[self._val]


#TODO: move this to another module
def sum_coordinate(c1,c2):
    return tuple(sum(x) for x in zip(c1, c2))

# absolute orientations
NORTH = AbsoluteOrientation(1)
EAST = AbsoluteOrientation(3)
SOUTH = AbsoluteOrientation(5)
WEST = AbsoluteOrientation(7)
NORTH_WEST = AbsoluteOrientation(0)
NORTH_EAST = AbsoluteOrientation(2)
SOUTH_EAST = AbsoluteOrientation(4)
SOUTH_WEST = AbsoluteOrientation(6)



# relative positions
FRONT = RelativeOrientation(0)
FRONT_LEFT = RelativeOrientation(-1)
FRONT_RIGHT = RelativeOrientation(1)
LEFT = RelativeOrientation(-2)
RIGHT = RelativeOrientation(2)
BACK_LEFT = RelativeOrientation(-3)
BACK_RIGHT = RelativeOrientation(3)
BACK = RelativeOrientation(4)