import json


class PMessage():
    _type = None
    _msg = None

    # for type
    T_COMMAND = "cmd"
    T_STATE_CHANGE = "stchange"
    T_ROBOT_MOVE = "robotmove"
    T_MAP_UPDATE = "mapupdate"
    T_SET_ROBOT_POS = "setrobotpos"
    T_SET_EXPLORE_TIME_LIMIT = "setexploretime"  # msg for this should be a int
    T_SET_EXPLORE_COVERAGE = "setexplorecoverage"  # msg for this should be a int
    T_EXPLORE_REMAINING_TIME = "exploreremainingtime"  # msg for this should be a int
    T_CUR_EXPLORE_COVERAGE = "curexplorecoverage"  # msg is int
    # TODO: for simulation only
    T_LOAD_MAP = "loadmap"  # msg should be map path

    # for msg
    M_START_EXPLORE = "explore"
    M_END_EXPLORE = "endexplore"
    M_MOVE_FORWARD = "mf"
    M_TURN_LEFT = "tl"
    M_TURN_RIGHT = "tr"
    M_START_FASTRUN = "run"
    M_REACH_END = "end"
    M_RESET = "reset"
    # TODO: remove this in production
    M_JUMP_EXPLORE = "jumpexplore"

    M_MOVE_INSTRUCTIONS = [M_MOVE_FORWARD, M_TURN_LEFT, M_TURN_RIGHT]

    def render_msg(self):
        """return message formatted in JSON"""
        return json.dumps({"type": self._type, "msg": self._msg})

    def __unicode__(self):
        return self.render_msg()

    def __str__(self):
        return self.render_msg()

    def __init__(self, **kwargs):
        """
        can either initialize via json by passing in `json_str`,
        or pass in `type` and `msg`
        """
        json_str = kwargs.get("json_str")
        if json_str:
            obj = json.loads(json_str)
            self._type = obj['type']
            self._msg = obj['msg']
        else:
            self._type = kwargs.get("type")
            self._msg = kwargs.get("msg")

    @staticmethod
    def load_messages_from_json(json_str):
        "json_str may be a concatenation of json, return a list of PMessage"
        import re

        json_pattern = re.compile(r'{[^{}]+}')
        json_strs = json_pattern.findall(json_str)
        return [PMessage(json_str=js) for js in json_strs]

    def equals(self, a_msg):
        return self._type == a_msg._type and self._msg == a_msg._msg

    def get_type(self):
        return self._type

    def get_msg(self):
        return self._msg

# common messages
START_EXPLORE = PMessage(type=PMessage.T_COMMAND, msg=PMessage.M_START_EXPLORE)
STATE_CHANGED_TO_EXPLORE = PMessage(type=PMessage.T_STATE_CHANGE, msg=PMessage.M_START_EXPLORE)
