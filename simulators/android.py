"""
test android client side
"""

import socket
from thread import start_new_thread
import time

from algorithms.maze_explore import MazeExploreAlgo
from common.robot import *
from common.network import *


class ClientSimulationApp():

    _text = None
    _mv_btn = None # button move forward
    _tl_btn = None # turn left
    _tr_btn = None # turn right
    _explore_btn = None
    _fastrun_btn = None # start fastest running
    _jump_explore_btn = None
    _reset_btn = None
    _explore_algo = None

    _map_ui = None
    _map_ref = [] #internal 2D representation of map
    _robot = None

    _client = None # SocketClient

    def __init__(self,root):
        # status text boxes
        self._text = Text(master=root,height=6)
        self._text.grid(row=0,column=0)
        # buttons
        self._button_frame = Frame(master=root)
        self._button_frame.grid(row=1,column=0)
        self._mv_btn = Button(master=self._button_frame,text="move forward",command=self.move_forward)
        self._mv_btn.grid(row=0,column=0)
        self._tl_btn = Button(master=self._button_frame,text="turn left",command=self.turn_left)
        self._tl_btn.grid(row=0,column=1)
        self._tr_btn = Button(master=self._button_frame,text="turn right",command=self.turn_right)
        self._tr_btn.grid(row=0,column=2)
        self._fastrun_btn = Button(master=self._button_frame,text="fast run",command=self.start_fast_run)
        self._fastrun_btn.grid(row=0,column=3)
        self._explore_btn = Button(master=self._button_frame,text="explore",command=self.start_exploration)
        self._explore_btn.grid(row=0,column=4)
        self._reset_btn = Button(master=self._button_frame,text="reset",command=self.reset)
        self._reset_btn.grid(row=0,column=5)
        #TODO: remove this in production
        self._jump_explore_btn = Button(master=self._button_frame,text="jump explore",command=self.jump_explore)
        self._jump_explore_btn.grid(row=0,column=6)
        # gui for set exploration time limit
        self._set_explore_time_limit_btn = Button(master=self._button_frame,text="set explore time limit",command=self.set_explore_time_limit)
        self._set_explore_time_limit_text = Text(master=self._button_frame,width=10,height=1)
        self._set_explore_time_limit_btn.grid(row=1,column=0)
        self._set_explore_time_limit_text.grid(row=1,column=1)
        # gui for set exploration coverage limit
        self._set_explore_coverage_limit_btn = Button(master=self._button_frame,text="set explore coverage limit",command=self.set_explore_coverage_limit)
        self._set_explore_coverage_limit_text = Text(master=self._button_frame,width=10,height=1)
        self._set_explore_coverage_limit_btn.grid(row=1,column=2)
        self._set_explore_coverage_limit_text.grid(row=1,column=3)
        # gui for displaying status
        self._explore_time_remain_label = Label(master=self._button_frame,text="Exploration time remaining:")
        self._explore_coverage_label = Label(master=self._button_frame,text="Coverage:")
        self._explore_time_remain_label.grid(row=2,column=0)
        self._explore_coverage_label.grid(row=2,column=1)
        # init map
        self._map_ref = MapRef()
        self._map_ref.load_map_from_file("zone.txt")
        self._map_frame = Frame(master=root)
        self._map_ui = MapUI(frame=self._map_frame,map_ref=self._map_ref)
        self._map_frame.grid(row=4,column=0)
        # init robot
        self._robot = RobotRef()
        self._robotUI = RobotUI(robot=self._robot,cells=self._map_ui.get_cells())
        # paint map
        self._map_ui.paint()
        # paint robot
        self._robot.refresh()
        # init algo
        self._explore_algo = MazeExploreAlgo(robot=self._robot,map_ref=self._map_ref)
        # start server
        self._client = SocketClient(server_addr=MOCK_SERVER_ADDR,server_port=ANDROID_SERVER_PORT)
        start_new_thread(self.start_session,())

    def set_explore_coverage_limit(self):
        coverage = int(self._set_explore_coverage_limit_text.get("1.0",END))
        self.send_data(con=self._client,type=PMessage.T_SET_EXPLORE_COVERAGE,data=coverage)

    def set_explore_time_limit(self):
        time_limit = int(self._set_explore_time_limit_text.get("1.0",END))
        self._explore_time_limit = time_limit
        self.send_data(con=self._client,type=PMessage.T_SET_EXPLORE_TIME_LIMIT,data=time_limit)


    def start_fast_run(self):
        # compute run commands
        self.send_command(PMessage.M_START_FASTRUN)

    def reset(self):
        self._map_ref.reset()
        self._robot.reset()
        self.send_command(PMessage.M_RESET)

    #TODO: remove this in production
    def jump_explore(self):
        self._map_ref.load_map_from_file("D:/map.txt")
        self._robot.refresh()
        self.send_command(PMessage.M_JUMP_EXPLORE)

    def start_exploration(self):
        self.send_command(PMessage.M_START_EXPLORE)

    def send_command_list(self,cmd_list):
        for cmd in cmd_list:
            self.send_command(cmd)
            time.sleep(1)

    def send_command(self,command):
        if (not self._client):
            raise Exception("socket not ready")
        self.send_data(con=self._client,type=PMessage.T_COMMAND,
                       data = command)
        self.show_status("Sent command : " + str(command))

    def move_forward(self):
        self.send_command(PMessage.M_MOVE_FORWARD)

    def turn_left(self):
        self.send_command(PMessage.M_TURN_LEFT)

    def turn_right(self):
        self.send_command(PMessage.M_TURN_RIGHT)

    def start_session(self):
        self._client.start()
        time.sleep(1)
        self.show_status("Rpi connected")
        self.serve_connection(self._client)

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
                    elif (msg_obj.get_type()==PMessage.T_ROBOT_MOVE):
                        self._map_ref.refresh()
                        self._robot.execute_command(msg_obj.get_msg())
                    elif(msg_obj.get_type()==PMessage.T_EXPLORE_REMAINING_TIME):
                        time_remain = msg_obj.get_msg()
                        self._explore_time_remain_label.config(text="Exploration remaining time:{}".format(time_remain))
                    elif(msg_obj.get_type()==PMessage.T_CUR_EXPLORE_COVERAGE):
                        coverage = msg_obj.get_msg()
                        self._explore_coverage_label.config(text="Coverage: {}".format(coverage))


    def process_data(self,recv_data):
        "update the map according to sensor data and return reply msg"
        sensor_values = [int(i) for i in recv_data.split(SENSOR_READING_DELIMITER)]
        self.update_map(sensor_values)


    def update_map(self,sensor_values):
        "update the map_ref and also the gui"
        clear_pos_list,obstacle_pos_list = self._robot.sense_area(sensor_values)
        self._map_ref.set_cell_list(pos_list=clear_pos_list,value=MapRef.CLEAR)
        self._map_ref.set_cell_list(pos_list=obstacle_pos_list,value=MapRef.OBSTACLE)

    def show_status(self,msg):
        self._text.insert(END,msg+"\n")


    def send_data(self,con,type,data):
        "con is a SocketClient object"
        msg = PMessage(type=type,msg=data)
        con.write(str(msg))
        print("msg sent: {}".format(msg))


def main():
    window = Tk()
    app = ClientSimulationApp(root=window)
    window.title("Android")
    window.mainloop()

main()