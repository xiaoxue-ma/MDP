from Tkinter import *
from thread import start_new_thread
import socket
import time

from common import *
from common.pmessage import PMessage
from simulators.robot import *
from common.amap import *


class AppSettings():
    """
    settings for ArduinoSimulation
    """
    SENSOR_DATA_DELAY = 0.5
    TEXTBOX_HEIGHT = 5
    MAP_FILE_NAME = "map.txt"
    ROBOT_ORI_LABEL = "Robot Orientation: {}"
    ROBOT_POS_LABEL = "Robot position: {},{}"
    VALID_CELL_VALUE = MapRef.VALID_CELL_VALUES
    VALID_INSTRUCTIONS = [PMessage.M_MOVE_FORWARD,PMessage.M_TURN_LEFT,PMessage.M_TURN_RIGHT,PMessage.M_START_EXPLORE,PMessage.M_START_FASTRUN]

class ArduinoSimulationApp(BaseObserver,AppSettings):
    # robot info
    _robot = None
    # 2d map info
    _map_ref = None
    # gui elements
    _map_ui = None # MapUI object
    _label_orientation = None
    _label_position = None
    _text_status = None
    _send_data_btn = None
    _map_frame = None
    # connection with rpi
    _connection = None
    _sending_sensor_data = False
    _sending_move_ack = False

    def __init__(self,root):
        # load map from file
        self._map_ref = MapRef()
        self._map_ref.load_map_from_file(self.MAP_FILE_NAME)
        # init map
        self._map_frame = Frame(master=root) # container
        self._map_ui = MapUI(frame=self._map_frame,map_ref=self._map_ref)
        self._map_ref.refresh()
        self._map_frame.grid(row=0,column=0)
        # init button
        self._send_data_btn = Button(master=root,text="send sensor data",command=self.send_sensor_data)
        self._send_data_btn.grid(row=2,column=0)
        # add this app as the listener of robot
        self._robot = RobotRef()
        self._robotUI = RobotUI(robot=self._robot,cells=self._map_ui.get_cells())
        self._robot.add_change_listener(self)
        self._robot.refresh()
        # init labels and text area
        info_frame = Frame(master=root)
        self.init_info_elements(root=info_frame)
        info_frame.grid(row=1,column=0)
        # start server
        start_new_thread(self.start_server,())

    def init_info_elements(self,root):
        self._label_orientation = Label(master=root,text="...")
        self._label_orientation.grid(row=0,column=0)
        self._label_position = Label(master=root,text="...")
        self._label_position.grid(row=1,column=0)
        self._text_status = Text(master=root,height=self.TEXTBOX_HEIGHT)
        self._text_status.grid(row=2,column=0)
        self.update()

    def send_sensor_data(self):
        "send sensor reading to client"
        readings = self._robot.get_sensor_readings(self._map_ref)
        self.show_status(str(readings))
        self.send_data(con=self._connection,type=PMessage.T_MAP_UPDATE,
                       data=",".join([str(i) for i in readings]))
        self.show_status("Readings sent")

    def start_server(self):
        # set up server socket
        time.sleep(1)
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        server_address = (MOCK_SERVER_ADDR,ARDUINO_SERVER_PORT)
        sock.bind(server_address)
        self.show_status("server started at {},{}".format(MOCK_SERVER_ADDR,ARDUINO_SERVER_PORT))
        # listening for connections
        sock.listen(1)
        connection,client_addr = sock.accept()
        self._connection = connection
        self.show_status("accept client: " + str(client_addr))
        self.serve_connection(connection)

    def serve_connection(self,conn):
        "get instructions from Rpi and execute"
        while True:
            msg =conn.recv(1024)
            if (msg):
                objs = PMessage.load_messages_from_json(msg)
                if (not objs): continue
                for msg_obj in objs:
                    print("received data: " + str(msg_obj))
                    instruction = self.decode_instruction(msg_obj)
                    if (instruction):
                        self.execute_instruction(instruction)
                        if (self._sending_sensor_data):
                            time.sleep(self.SENSOR_DATA_DELAY)
                            self.send_sensor_data()
                        if (self._sending_move_ack):
                            self.send_data(con=conn,type=PMessage.T_ROBOT_MOVE,data=instruction)
                    else: self.show_status("Instruction cannot be decoded!")

    def decode_instruction(self,msg):
        "return the normal representation of instruction, None if cannot"
        instruct = msg.get_msg()
        if (instruct in self.VALID_INSTRUCTIONS):
            return instruct

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

    def show_status(self,msg):
        self._text_status.insert(END,msg+"\n")

    def update(self):
        "update method as an observer"
        pos = self._robot.get_position()
        ori = self._robot.get_orientation()
        self._label_position.config(text=self.ROBOT_POS_LABEL.format(pos[0],pos[1]))
        self._label_orientation.config(text=self.ROBOT_ORI_LABEL.format(ori.get_name()))

    def send_data(self,con,type,data):
        msg = PMessage(type=type,msg=data)
        con.sendall(str(msg))

def main():
    window = Tk()
    app = ArduinoSimulationApp(root=window)
    window.title("arduino")
    window.mainloop()

main()