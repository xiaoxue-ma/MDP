from thread import start_new_thread
import socket
import time

from common.robot import *
from common.amap import *

from simulators.controllers import ArduinoController

class AppSettings():
    """
    settings for Arduino Simulation
    """
    TEXTBOX_HEIGHT = 5
    ROBOT_ORI_LABEL = "Robot Orientation: {}"
    ROBOT_POS_LABEL = "Robot position: {},{}"


class ArduinoSimulationApp(BaseObserver,AppSettings):
    _controller = None # ArduinoController
    # gui elements
    _map_ui = None # MapUI object
    _label_orientation = None
    _label_position = None
    _text_status = None
    _send_data_btn = None
    _map_frame = None

    def __init__(self,root):
        # load map from file
        _map_ref = MapRef()
        # init map
        self._map_frame = Frame(master=root) # container
        self._map_ui = MapUI(frame=self._map_frame,map_ref=_map_ref)
        self._map_frame.grid(row=0,column=0)
        # add this app as the listener of robot
        _robot = RobotRef()
        self._robotUI = RobotUI(robot=_robot,cells=self._map_ui.get_cells())
        #_robot.add_change_listener(self)
        # init controller
        self._controller = ArduinoController(map_ref=_map_ref,robot_ref=_robot)
        self._controller.add_change_listener(self)
        # init button
        self._control_frame = Frame(master=root)
        self._control_frame.grid(row=1,column=0)
        self._init_control_frame(self._control_frame)

        # init labels and text area
        info_frame = Frame(master=root)
        self.init_info_elements(root=info_frame)
        info_frame.grid(row=2,column=0)
        self._controller.run()

    def init_info_elements(self,root):
        self._label_orientation = Label(master=root,text="...")
        self._label_orientation.grid(row=0,column=0)
        self._label_position = Label(master=root,text="...")
        self._label_position.grid(row=1,column=0)
        self._text_status = Text(master=root,height=self.TEXTBOX_HEIGHT)
        self._text_status.grid(row=2,column=0)
        scrollb = Scrollbar(root, command=self._text_status.yview)
        scrollb.grid(row=2, column=1, sticky='nsew')
        self._text_status['yscrollcommand'] = scrollb.set
        self.update()

    def _init_control_frame(self,fr):
        self._send_data_btn = Button(master=fr,text="send sensor data",command=self._controller.send_sensor_data)
        self._send_data_btn.grid(row=0,column=0)
        self._load_map_btn = Button(master=fr,text="load map",command=self.load_map)
        self._load_map_btn.grid(row=0,column=1)
        self._load_map_text = Text(master=fr,height=1,width=10)
        self._load_map_text.grid(row=0,column=2)
        self._switch_sensor_btn = Button(master=fr,text="switch sensor",command=self.toggle_sensor)
        self._switch_sensor_btn.grid(row=0,column=3)

    def toggle_sensor(self):
        self._controller.toggle_sensor()

    def load_map(self):
        filename = self._load_map_text.get("1.0",END)[:-1]
        self._controller.load_map(filename)

    def update(self,data=None):
        "update method as an observer"
        if (data):
            self._text_status.insert(END,data+"\n")
        pos = self._controller.get_robot_pos()
        ori = self._controller.get_robot_ori()
        self._label_position.config(text=self.ROBOT_POS_LABEL.format(pos[0],pos[1]))
        self._label_orientation.config(text=self.ROBOT_ORI_LABEL.format(ori.get_name()))

def main():
    window = Tk()
    app = ArduinoSimulationApp(root=window)
    window.title("arduino")
    window.mainloop()

main()