from common.pmessage import PMessage

class Orientation():
    _val = 0

    def __init__(self,val):
        "should not be called outside the class"
        self._val = val

    def get_value(self):
        return self._val

    def get_name(self):
        raise NotImplementedError()

class AbsoluteOrientation(Orientation):
    """
    This should be a singleton pattern, only use get_instance() to get object
    internally, absolute orientation is represented as eight numbers as follows
    0  1      2
    7 center  3  ^up
    6  5      4
    """
    POS_CHANGE_DICT = {0:(-1,-1),1:(0,-1),2:(1,-1),3:(1,0),4:(1,1),5:(0,1),6:(-1,1),7:(-1,0)}
    ACTION_TO_ORI_CHANGE = {PMessage.M_TURN_LEFT:-2,PMessage.M_TURN_RIGHT:2,PMessage.M_MOVE_FORWARD:0}
    ORI_VERBOSE = {1:'up',5:'down',7:'left',3:'right'}

    _instances = []

    @staticmethod
    def get_instance(val):
        for instance in AbsoluteOrientation._instances:
            if (instance.get_value()==val):
                return instance
        # create new instance
        new_instance = AbsoluteOrientation(val)
        AbsoluteOrientation._instances.append(new_instance)
        return new_instance

    def to_pos_change(self):
        "return tuple representing the position change relative to the center"
        return self.POS_CHANGE_DICT[self._val]

    def if_applied_action(self,action):
        "return the resulting ori if action applied"
        new_val = (self._val + self.ACTION_TO_ORI_CHANGE[action])%8
        return AbsoluteOrientation.get_instance(new_val)

    def get_minimum_turns_to(self,a_ori):
        "return number of turns needed to be made to reach a_ori"
        val_diff = (a_ori._val-self._val)%8
        val_diff = min(val_diff,8-val_diff)
        return int(val_diff/2)

    def to_left(self):
        return AbsoluteOrientation.get_instance((self._val+2*3)%8)

    def to_right(self):
        return AbsoluteOrientation.get_instance((self._val+2*1)%8)

    def to_back(self):
        return AbsoluteOrientation.get_instance((self._val+2*2)%8)

    @staticmethod
    def get_ori_at_dest(start_pos,dest_pos):
        "return the resulting ori if the robot go from start to dest"
        pos_diff = (dest_pos[0]-start_pos[0],dest_pos[1]-start_pos[1])
        LOOPUP_DICT = {(0,-1):1,(1,0):3,(0,1):5,(-1,0):7}
        new_val = LOOPUP_DICT[pos_diff]
        return AbsoluteOrientation.get_instance(new_val)

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

    def __unicode__(self):
        return self.get_name()

    def __str__(self):
        return self.get_name()

class RelativeOrientation(Orientation):
    """
    internally, relative orientation is represented as eight numbers as follows
    -1  0      1
    -2  center 2  ^front
    -3  4      3
    """

    ORI_VERBOSE = {-1:'front-left',0:'front',1:'front-right',-2:'left',2:'right',-3:'back-left',3:'back-right',4:'back'}

    _instances = []

    @staticmethod
    def get_instance(val):
        for instance in RelativeOrientation._instances:
            if (instance.get_value()==val):
                return instance
        # create new instance
        new_instance = RelativeOrientation(val)
        RelativeOrientation._instances.append(new_instance)
        return new_instance

    def get_actual_abs_ori(self,ref_front_ori):
        "return absolute orientation, if front_major is True, front-left and front-right will be considered as front"
        val = self._val
        abs_val = (val + ref_front_ori.get_value())%8
        return AbsoluteOrientation.get_instance(abs_val)

    def to_pos_change(self,rel_front_ori):
        abs_val = (self._val + rel_front_ori.get_value())%8
        return AbsoluteOrientation.get_instance(abs_val).to_pos_change()

    def __unicode__(self):
        return self.ORI_VERBOSE[self._val]

    def __str__(self):
        return self.ORI_VERBOSE[self._val]


#TODO: move this to another module
def sum_coordinate(c1,c2):
    return tuple(sum(x) for x in zip(c1, c2))

# absolute orientations
NORTH = AbsoluteOrientation.get_instance(1)
EAST = AbsoluteOrientation.get_instance(3)
SOUTH = AbsoluteOrientation.get_instance(5)
WEST = AbsoluteOrientation.get_instance(7)
NORTH_WEST = AbsoluteOrientation.get_instance(0)
NORTH_EAST = AbsoluteOrientation.get_instance(2)
SOUTH_EAST = AbsoluteOrientation.get_instance(4)
SOUTH_WEST = AbsoluteOrientation.get_instance(6)



# relative positions
FRONT = RelativeOrientation.get_instance(0)
FRONT_LEFT = RelativeOrientation.get_instance(-1)
FRONT_RIGHT = RelativeOrientation.get_instance(1)
LEFT = RelativeOrientation.get_instance(-2)
RIGHT = RelativeOrientation.get_instance(2)
BACK_LEFT = RelativeOrientation.get_instance(-3)
BACK_RIGHT = RelativeOrientation.get_instance(3)
BACK = RelativeOrientation.get_instance(4)