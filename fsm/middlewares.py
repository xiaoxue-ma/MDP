import os
from abc import abstractmethod,ABCMeta
from common.popattern import BasePublisher
from common.utils import SimpleQueue,get_or_exception,create_or_append_file
from interfaces.config import VALID_LABELS,CMD_SOURCES,ARDUINO_LABEL
from common.pmessage import PMessage
from common.amap import MapSetting
from common.debug import debug,DEBUG_MIDDLEWARE


class BaseMiddleware(object):
    """
    abstract class
    middleware is used to encapsulate common input processing logic
    """
    __metaclass__ = ABCMeta

    _consume_input = False # if True, the input will not be processed by the middlewares after this
    _state = None # State object
    _map_ref = None # MapRef object
    _robot_ref = None # RobotRef object

    def __init__(self,*args,**kwargs):
        "state param must be passed"
        self._consume_input = kwargs.get("consume_input",False)
        self._state = get_or_exception(kwargs,"state","Middleware class cannot be instantiated without the `state` param")
        self._map_ref = self._state.get_map_ref()
        self._robot_ref = self._state.get_robot_ref()

    def process(self,label,pmsg):
        """
        :param label: ANDROID_LABEL or ARDUINO_LABEL or PC_LABEL
        :param pmsg: PMessage object
        :return: cmd_list,data_list
        """
        if (not label in VALID_LABELS):
            debug("label '{}' is not valid".format(label),DEBUG_MIDDLEWARE)
            return [],[]
        elif (not isinstance(pmsg,PMessage)):
            debug("object {} is not a PMessage object".format(pmsg),DEBUG_MIDDLEWARE)
            return [],[]
        return self.process_input(label,pmsg)

    @abstractmethod
    def process_input(self,label,msg):
        "label is str, msg guaranteed to be PMessage object"
        raise NotImplementedError()

    def is_consume_input(self):
        return self._consume_input

class AckMiddleware(BaseMiddleware):
    """
    middleware for receiving ack and making proper response
    """
    _ack_q = None # queue of {'label':'','msg':PMessage_object,'call_back':some_function,'args':[]}

    def __init__(self,*args,**kwargs):
        super(AckMiddleware,self).__init__(*args,**kwargs)
        self._ack_q = SimpleQueue()

    def process_input(self,label,msg):
        "check whether the input is the expected ack message"
        if (not self._ack_q.is_empty()):
            ack_item = self._ack_q.peek()
            if (ack_item['label'] == label and msg.equals(ack_item['msg'])):
                call_back = ack_item['call_back']
                call_back_args = ack_item['args']
                self._ack_q.dequeue()
                try:
                    cmd_list,data_list = call_back(*call_back_args) if call_back_args else call_back()
                    return cmd_list,data_list
                except Exception as e:
                    debug("ack call back function doesn't return two lists: {}".format(e),DEBUG_MIDDLEWARE)
                    return [],[]

        return [],[]

    def add_expected_ack(self,label,msg,call_back,args=None):
        "msg is PMessage, label is str, call_back is a function"
        self._ack_q.enqueue({
            'label':label,
            'msg':msg,
            'call_back':call_back,
            'args':args if args else []
        })

class MoveCommandMiddleware(AckMiddleware):
    """
    class for handling move commands, wait for arduino ack before sending to android
    """
    def process_input(self,label,msg):
        # process ack
        cmd_ls,data_ls = super(MoveCommandMiddleware,self).process_input(label,msg)
        if (cmd_ls or data_ls):
            return cmd_ls,data_ls
        # process command
        elif (msg.get_type()==PMessage.T_COMMAND and msg.get_msg() in PMessage.M_MOVE_INSTRUCTIONS and label in CMD_SOURCES):
            # send command to arduino, wait till ack and then send update to android
            self.add_expected_ack(label=ARDUINO_LABEL,msg=PMessage(type=PMessage.T_ROBOT_MOVE,msg=msg.get_msg()),call_back=self.move_ack_call_back,args=[msg.get_msg()])
            return [msg],[]
        return [],[]

    def move_ack_call_back(self,move):
        self._robot_ref.execute_command(move)
        self._map_ref.set_fixed_cells(self._robot_ref.get_occupied_postions(),MapSetting.CLEAR)
        #return [],[PMessage(type=PMessage.T_ROBOT_MOVE,msg=move)]
        return [],[]

class MapUpdateMiddleware(BaseMiddleware):
    """
    class for handling map update from arduino
    """
    _consume_input = False
    # map update strategy
    _overwrite_obstacle = False
    _overwrite_clear = True

    # map update format
    map_update_sent_in_list = False

    # for debugging purpose
    _SAVE_MAP_TRACE = False
    map_trace_num = 0
    map_trace_file_name = "map-trace.txt"

    def process_input(self,label,msg):
        if (label!=ARDUINO_LABEL or msg.get_type()!=PMessage.T_MAP_UPDATE):
            return [],[]
        sensor_values = map(int,msg.get_msg().split(","))
        clear_pos_list,obstacle_pos_list = self.update_map(sensor_values)
        map_update_to_send = [clear_pos_list,obstacle_pos_list] if self.map_update_sent_in_list else ",".join([str(i) for i in sensor_values])
        if (self._SAVE_MAP_TRACE):
            self.save_map_trace()
        return [],[]
        # return [],[PMessage(type=PMessage.T_MAP_UPDATE,msg=map_update_to_send)]

    def update_map(self,sensor_values):
        "update the map_ref according to received sensor readings"
        clear_pos_list,obstacle_pos_list = self._robot_ref.sense_area(sensor_values)
        self._map_ref.set_cell_list(pos_list=clear_pos_list,value=MapSetting.CLEAR,maintain_obstacle=(not self._overwrite_obstacle))
        self._map_ref.set_cell_list(pos_list=obstacle_pos_list,value=MapSetting.OBSTACLE,maintain_clear=(not self._overwrite_clear))
        return clear_pos_list,obstacle_pos_list

    def save_map_trace(self):
        # clear the trace file
        if (self.map_trace_num==0):
            f = open(self.map_trace_file_name,"w")
            f.close()
        # generate and save map trace
        map_str = self.get_map_trace(map_ref=self._map_ref,robot_ref=self._robot_ref)
        map_str = "\n\n-----------------# {}-------------------------\n\n{}".format(self.map_trace_num,map_str)
        self.map_trace_num +=1
        create_or_append_file(self.map_trace_file_name,map_str)

    def get_map_trace(self,map_ref,robot_ref):
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

class MapUpdateMiddlewareUsingMapBuffer(MapUpdateMiddleware):
    """
    To use this, map_ref must be a MapRefWithBuffer object
    For every map update, a list of positions will be sent
    """
    def process_input(self,label,msg):
        cmd_ls,data_ls = super(MapUpdateMiddlewareUsingMapBuffer,self).process_input(label,msg)
        if (hasattr(self._map_ref,"retrieve_updated_cells")):
            cells = self._map_ref.retrieve_updated_cells()
            if (cells):
                return [],[]
                # return [],[PMessage(type=PMessage.T_UPDATE_MAP_STATUS,msg="|".join(["{},{},{}".format(x,y,o) for x,y,o in cells]))]
            else:
                return [],[]
        else:
            return cmd_ls,data_ls

# class MapUpdateMiddlewareAsPublisher(MapUpdateMiddleware,BasePublisher):
#     """
#     wrapper class to provide observer-pattern functions
#     """
#     def __init__(self,*args,**kwargs):
#         super(MapUpdateMiddlewareAsPublisher,self).__init__(*args,**kwargs)
#         listeners = kwargs.get("listeners",[])
#         for l in listeners:
#             self.add_change_listener(l)
#
#     def update_map(self,sensor_values):
#         val = super(MapUpdateMiddlewareAsPublisher,self).update_map(sensor_values)
#         self.notify()
#         return val

class ResetMiddleware(BaseMiddleware):
    """
    handle Reset command
    """

    def process_input(self,label,msg):
        if (label in CMD_SOURCES and msg.get_type()==PMessage.T_COMMAND and msg.get_msg()==PMessage.M_RESET):
            self._state.reset_machine()
            return [PMessage(type=PMessage.T_COMMAND,msg=PMessage.M_RESET)],[]
        return [],[]