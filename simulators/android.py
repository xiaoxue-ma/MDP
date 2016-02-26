"""
test android client side
"""

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
    _map_ref = None #internal 2D representation of map
    _robot = None

    _client = None # SocketClient

    def __init__(self,root):
        # status text boxes
        self._info_frame =  Frame(master=root)
        self._info_frame.grid(row=0,column=0)
        self._init_info_frame(fr=self._info_frame)
        # buttons
        self._button_frame = Frame(master=root)
        self._button_frame.grid(row=1,column=0)
        self._init_btn_frame(fr=self._button_frame)
        # gui for set exploration time limit
        self._limit_frame =  Frame(master=root)
        self._limit_frame.grid(row=2,column=0)
        self._init_limit_frame(fr=self._limit_frame)
        # load and save map
        self._io_frame =  Frame(master=root)
        self._io_frame.grid(row=3,column=0)
        self._init_io_frame(fr=self._io_frame)
        # init map
        self._map_frame = Frame(master=root)
        self._map_frame.grid(row=4,column=0)
        self._init_map_frame(fr=self._map_frame)
        # init algo
        self._explore_algo = MazeExploreAlgo(robot=self._robot,map_ref=self._map_ref)
        # start server
        self._client = SocketClient(server_addr=MOCK_SERVER_ADDR,server_port=ANDROID_SERVER_PORT)
        start_new_thread(self.start_session,())

    def _init_info_frame(self,fr):
        self._text = Text(master=fr,height=4)
        self._text.grid(row=0,column=0,columnspan=2)
        scrollb = Scrollbar(fr, command=self._text.yview)
        scrollb.grid(row=0, column=1, sticky='nsew')
        self._text['yscrollcommand'] = scrollb.set
        self._cur_info = Label(master=fr,bg="yellow",text="welcome")
        self._cur_info.grid(row=1,column=0,columnspan=2)
        # gui for displaying status
        self._explore_time_remain_label = Label(master=fr,text="Exploration time remaining:")
        self._explore_coverage_label = Label(master=fr,text="Coverage:")
        self._explore_time_remain_label.grid(row=2,column=0,columnspan=1)
        self._explore_coverage_label.grid(row=2,column=1,columnspan=2)

    def _init_btn_frame(self,fr):
        self._mv_btn = Button(master=fr,text="move forward",command=self.move_forward)
        self._mv_btn.grid(row=0,column=0)
        self._tl_btn = Button(master=fr,text="turn left",command=self.turn_left)
        self._tl_btn.grid(row=0,column=1)
        self._tr_btn = Button(master=fr,text="turn right",command=self.turn_right)
        self._tr_btn.grid(row=0,column=2)
        self._fastrun_btn = Button(master=fr,text="fast run",command=self.start_fast_run)
        self._fastrun_btn.grid(row=0,column=3)
        self._explore_btn = Button(master=fr,text="explore",command=self.start_exploration)
        self._explore_btn.grid(row=0,column=4)
        self._reset_btn = Button(master=fr,text="reset",command=self.reset)
        self._reset_btn.grid(row=0,column=5)
        self._endexplore_btn = Button(master=fr,text="end explore",command=self.end_explore)
        self._endexplore_btn.grid(row=0,column=6)

    def _init_limit_frame(self,fr):
        self._set_explore_time_limit_btn = Button(master=fr,text="set explore time limit",command=self.set_explore_time_limit)
        self._set_explore_time_limit_text = Text(master=fr,width=10,height=1)
        self._set_explore_time_limit_btn.grid(row=0,column=0)
        self._set_explore_time_limit_text.grid(row=0,column=1)
        # gui for set exploration coverage limit
        self._set_explore_coverage_limit_btn = Button(master=fr,text="set explore coverage limit",command=self.set_explore_coverage_limit)
        self._set_explore_coverage_limit_text = Text(master=fr,width=10,height=1)
        self._set_explore_coverage_limit_btn.grid(row=0,column=2)
        self._set_explore_coverage_limit_text.grid(row=0,column=3)

    def _init_io_frame(self,fr):
        self._load_map_btn = Button(master=fr,text="load map",command=self.load_map)
        self._load_map_btn.grid(row=0,column=0)
        self._load_map_text = Text(master=fr,height=1,width=10)
        self._load_map_text.grid(row=0,column=1)
        self._save_map_btn = Button(master=fr,text="save map",command=self.save_map)
        self._save_map_btn.grid(row=0,column=2)
        self._save_map_text = Text(master=fr,height=1,width=10)
        self._save_map_text.grid(row=0,column=3)
        self._set_robot_pos_btn = Button(master=fr,text="set robot pos",command=self.set_robot_pos)
        self._set_robot_pos_btn.grid(row=0,column=4)
        self._set_robot_pos_text = Text(master=fr,height=1,width=10)
        self._set_robot_pos_text.grid(row=0,column=5)

    def _init_map_frame(self,fr):
        self._map_ref = MapRef()
        self._map_ui = MapUI(frame=fr,map_ref=self._map_ref)
        # init robot
        self._robot = RobotRef()
        self._robotUI = RobotUI(robot=self._robot,cells=self._map_ui.get_cells())
        self.reset(send_command=False)

    def set_explore_coverage_limit(self):
        coverage = int(self._set_explore_coverage_limit_text.get("1.0",END))
        self.send_data(con=self._client,type=PMessage.T_SET_EXPLORE_COVERAGE,data=coverage)
        self.show_status("Coverage limit set to {}".format(coverage))

    def set_explore_time_limit(self):
        time_limit = int(self._set_explore_time_limit_text.get("1.0",END))
        self._explore_time_limit = time_limit
        self.send_data(con=self._client,type=PMessage.T_SET_EXPLORE_TIME_LIMIT,data=time_limit)
        self.show_status("Exploration time limit set to {} s".format(time_limit))

    def set_robot_pos(self):
        msg = self._set_robot_pos_text.get("1.0",END)[:-1]
        x,y=msg.split(",")
        self.send_data(con=self._client,type=PMessage.T_SET_ROBOT_POS,data=msg)
        self._map_ref.refresh()
        self._robot.set_position((int(x),int(y)))

    def end_explore(self):
        self.send_data(con=self._client,type=PMessage.T_COMMAND,data=PMessage.M_END_EXPLORE)
        self.show_status("Exploration ended")

    def load_map(self):
        map_file_path = self._load_map_text.get("1.0",END)[:-1]
        self._map_ref.load_map_from_file(map_file_path)
        self._robot.refresh()
        print("map loaded")
        self.send_data(con=self._client,type=PMessage.T_LOAD_MAP,data=map_file_path)

    def save_map(self):
        map_file_path = self._save_map_text.get("1.0",END)[:-1]
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
        self._cur_info.config(text=msg)

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