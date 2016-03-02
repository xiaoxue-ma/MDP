import time
from thread import start_new_thread

from common.pmessage import PMessage
from common.amap import MapRef,MapSetting
from common.network import SocketClient
from common.popattern import BasePublisher
from common.constants import *

class BaseSimulatorController():
    _robot = None # RobotRef object
    _map_ref = None # MapRef object
    _client = None # SocketClient Object

    def __init__(self,**kwargs):
        self._map_ref = kwargs.get("map_ref")
        self._robot = kwargs.get("robot_ref")

    def run(self):
        # init client connection
        self._client = SocketClient(server_addr=self.get_server_addr(),server_port=self.get_server_port())
        start_new_thread(self.start_session,())

    def start_session(self):
        self._client.start()
        self.serve_connection(self._client)

    def send_data(self,type,data):
        msg = PMessage(type=type,msg=data)
        self._client.write(str(msg))

    ########## methods to be implemented by subclass #############
    def serve_connection(self,con):
        raise NotImplementedError("logic for serving connection not specified")

    def get_server_addr(self):
        return MOCK_SERVER_ADDR

    def get_server_port(self):
        raise NotImplementedError("server port not specified")

class ArduinoController(BaseSimulatorController):
    """
    controlling the internal logic of arduino simulator
    """
    SENSOR_DATA_DELAY = 0
    MAP_FILE_NAME = "map-1.bin"
    VALID_CELL_VALUE = MapRef.VALID_CELL_VALUES
    VALID_INSTRUCTIONS = [PMessage.M_MOVE_FORWARD,PMessage.M_TURN_LEFT,PMessage.M_TURN_RIGHT,PMessage.M_START_EXPLORE,PMessage.M_START_FASTRUN,PMessage.M_RESET]

    _sending_sensor_data = False
    _sending_move_ack = False

    def __init__(self,**kwargs):
        self._map_ref = kwargs.get("map_ref")
        self._robot = kwargs.get("robot_ref")
        self._map_ref.load_map_from_file(self.MAP_FILE_NAME)

    def get_server_port(self):
        return ARDUINO_SERVER_PORT

    def send_sensor_data(self):
        "send sensor reading to client"
        readings = self._robot.get_sensor_readings(self._map_ref)
        self.show_status(str(readings))
        self.send_data(type=PMessage.T_MAP_UPDATE,
                       data=",".join([str(i) for i in readings]))
        self.show_status("Readings sent")

    def serve_connection(self,conn):
        "get instructions from Rpi and execute"
        while True:
            msg =conn.read()
            if (msg):
                objs = PMessage.load_messages_from_json(msg)
                if (not objs): continue
                for msg_obj in objs:
                    print("received data: " + str(msg_obj))
                    if (msg_obj.get_type()==PMessage.T_SET_ROBOT_POS):
                        x,y=msg_obj.get_msg().split(",")
                        self._map_ref.refresh()
                        self._robot.set_position((int(x),int(y)))
                        self.show_status("Robot position set to {},{}".format(x,y))
                        continue
                    instruction = self.decode_instruction(msg_obj)
                    if (instruction):
                        self.execute_instruction(instruction)
                        if (self._sending_sensor_data):
                            time.sleep(self.SENSOR_DATA_DELAY)
                            self.send_sensor_data()
                        if (self._sending_move_ack):
                            self.send_data(type=PMessage.T_ROBOT_MOVE,data=instruction)
                    else: self.show_status("Instruction cannot be decoded!")

    def decode_instruction(self,msg):
        return msg.get_msg()

    def execute_instruction(self,instruct):
        "move the robot accordingly"
        if (instruct==PMessage.M_TURN_RIGHT):
            self._robot.turn_right()
        elif (instruct==PMessage.M_TURN_LEFT):
            self._robot.turn_left()
        elif(instruct==PMessage.M_MOVE_FORWARD):
            self._map_ref.refresh()
            self._robot.move_forward()
        elif(instruct==PMessage.M_START_EXPLORE):self._sending_sensor_data=True
        elif (instruct==PMessage.M_END_EXPLORE): self._sending_sensor_data = False
        elif(instruct==PMessage.M_START_FASTRUN): self._sending_move_ack=True
        elif(instruct==PMessage.M_RESET):self.reset()

    def reset(self):
        self._sending_sensor_data = False
        self._sending_move_ack = False
        self._map_ref.load_map_from_file(self.MAP_FILE_NAME)
        self._robot.reset()

    def show_status(self,msg):
        print(msg)

    def load_map(self,filename):
        self._map_ref.load_map_from_file(filename)
        self._robot.refresh()

    def get_robot_pos(self):
        return self._robot.get_position()

    def get_robot_ori(self):
        return self._robot.get_orientation()


class AndroidController(BasePublisher,BaseSimulatorController):
    _map_ref = None #internal 2D representation of map
    _robot = None
    _client = None # SocketClient
    _explore_remaining_time = 0
    _cur_explore_coverage = 0

    _MAP_UPDATE_IN_LIST = False

    def get_server_port(self):
        return ANDROID_SERVER_PORT

    def serve_connection(self,con):
        while True:
            data =con.read()
            if (data):
                objs = PMessage.load_messages_from_json(data)
                if (not objs): continue
                for msg_obj in objs:
                    print("received data: " + str(msg_obj))
                    if (msg_obj.get_type()==PMessage.T_MAP_UPDATE):
                        self.process_data(msg_obj.get_msg())
                        self._robot.refresh()
                    elif (msg_obj.get_type()==PMessage.T_STATE_CHANGE):
                        self.show_status("status changed to :{}".format(msg_obj.get_msg()))
                    elif (msg_obj.get_type()==PMessage.T_ROBOT_MOVE and msg_obj.get_msg()):
                        pos_list = self._robot.get_occupied_postions()
                        self._map_ref.notify(pos_list)
                        self._robot.execute_command(msg_obj.get_msg())
                    elif(msg_obj.get_type()==PMessage.T_EXPLORE_REMAINING_TIME):
                        self._explore_remaining_time = msg_obj.get_msg()
                        self.notify()
                    elif(msg_obj.get_type()==PMessage.T_CUR_EXPLORE_COVERAGE):
                        self._cur_explore_coverage = msg_obj.get_msg()
                        self.notify()

    def get_cur_coverage(self):
        return self._cur_explore_coverage

    def get_exploration_remaining_time(self):
        return self._explore_remaining_time

    def set_explore_coverage_limit(self,limit):
        self.send_data(type=PMessage.T_SET_EXPLORE_COVERAGE,data=limit)
        self.show_status("Coverage limit set to {}".format(limit))

    def set_explore_speed(self,num_steps_per_sec):
        delay = int(10.0/num_steps_per_sec) / 10.0
        self.show_status("Speed set to {} steps per second".format(num_steps_per_sec))
        self.send_data(type=PMessage.T_SET_EXPLORE_SPEED,data=delay)

    def set_explore_time_limit(self,time_limit):
        self._explore_time_limit = time_limit
        self.send_data(type=PMessage.T_SET_EXPLORE_TIME_LIMIT,data=time_limit)
        self.show_status("Exploration time limit set to {} s".format(time_limit))

    def set_robot_pos(self,x,y):
        self.send_data(type=PMessage.T_SET_ROBOT_POS,data="{},{}".format(x,y))
        self._map_ref.refresh()
        self._robot.set_position((int(x),int(y)))

    def end_explore(self):
        self.send_data(type=PMessage.T_COMMAND,data=PMessage.M_END_EXPLORE)
        self.show_status("Exploration ended")

    def load_map(self,map_file_path):
        self._map_ref.load_map_from_file(map_file_path)
        self._robot.refresh()
        print("map loaded")
        self.send_data(type=PMessage.T_LOAD_MAP,data=map_file_path)

    def save_map(self,map_file_path):
        self._map_ref.save_map_to_file(map_file_path)
        self.show_status("Map saved")

    def start_fast_run(self):
        # compute run commands
        self.send_command(PMessage.M_START_FASTRUN)

    def reset(self,send_command=True):
        self._map_ref.reset()
        self._robot.reset()
        self._map_ref.set_cell_list(pos_list=self._robot.get_occupied_postions(),
                                    value=MapSetting.CLEAR)
        self._robot.refresh()
        if (send_command):
            self.send_command(PMessage.M_RESET)

    def start_exploration(self):
        self.send_command(PMessage.M_START_EXPLORE)

    def send_command(self,command):
        if (not self._client):
            raise Exception("socket not ready")
        self.send_data(type=PMessage.T_COMMAND,
                       data = command)
        self.show_status("Sent command : " + str(command))

    def move_forward(self):
        self.send_command(PMessage.M_MOVE_FORWARD)

    def turn_left(self):
        self.send_command(PMessage.M_TURN_LEFT)

    def turn_right(self):
        self.send_command(PMessage.M_TURN_RIGHT)

    def process_data(self,recv_data):
        "update the map according to sensor data and return reply msg"
        if (self._MAP_UPDATE_IN_LIST):
            clear_pos_list=recv_data[0]
            obstacle_pos_list =recv_data[1]
            self._map_ref.set_cell_list(pos_list=clear_pos_list,value=MapSetting.CLEAR,notify=True)
            self._map_ref.set_cell_list(pos_list=obstacle_pos_list,value=MapSetting.OBSTACLE,notify=True)
        else:
            sensor_values = [int(i) for i in recv_data.split(SENSOR_READING_DELIMITER)]
            self.update_map(sensor_values)

    # deprecated
    def update_map(self,sensor_values):
        "update the map_ref and also the gui"
        clear_pos_list,obstacle_pos_list = self._robot.sense_area(sensor_values)
        self._map_ref.set_cell_list(pos_list=clear_pos_list,value=MapRef.CLEAR)
        self._map_ref.set_cell_list(pos_list=obstacle_pos_list,value=MapRef.OBSTACLE)

    def show_status(self,msg):
        print(msg)