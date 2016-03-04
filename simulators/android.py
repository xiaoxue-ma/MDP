"""
test android client side
"""

import time

from algorithms.maze_explore import MazeExploreAlgo
from common.robot import *
from common.network import *

from simulators.controllers import AndroidController


class ClientSimulationApp(BaseObserver):

    _text = None
    _mv_btn = None # button move forward
    _tl_btn = None # turn left
    _tr_btn = None # turn right
    _explore_btn = None
    _fastrun_btn = None # start fastest running
    _jump_explore_btn = None
    _reset_btn = None

    _map_ui = None

    _controller = None # AndroidController

    def __init__(self,root):
        # init controller
        map_ref = MapRef()
        robot = RobotRef()
        self._controller = AndroidController(map_ref=map_ref,robot_ref=robot)
        self._controller.add_change_listener(self)
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
        # init map ui
        self._map_frame = Frame(master=root)
        self._map_frame.grid(row=4,column=0)
        self._init_map_frame(fr=self._map_frame,map_ref=map_ref,robot_ref=robot)
        # init controller
        self._controller.run()

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
        self._mv_btn = Button(master=fr,text="move forward",command=self._controller.move_forward)
        self._mv_btn.grid(row=0,column=0)
        self._tl_btn = Button(master=fr,text="turn left",command=self._controller.turn_left)
        self._tl_btn.grid(row=0,column=1)
        self._tr_btn = Button(master=fr,text="turn right",command=self._controller.turn_right)
        self._tr_btn.grid(row=0,column=2)
        self._fastrun_btn = Button(master=fr,text="fast run",command=self._controller.start_fast_run)
        self._fastrun_btn.grid(row=0,column=3)
        self._explore_btn = Button(master=fr,text="explore",command=self._controller.start_exploration)
        self._explore_btn.grid(row=0,column=4)
        self._reset_btn = Button(master=fr,text="reset",command=self._controller.reset)
        self._reset_btn.grid(row=0,column=5)
        self._endexplore_btn = Button(master=fr,text="end explore",command=self._controller.end_explore)
        self._endexplore_btn.grid(row=0,column=6)
        self._set_speed_btn = Button(master=fr,text="set speed",command=self.set_explore_speed)
        self._set_speed_btn.grid(row=0,column=7)
        self._set_speed_text = Text(master=fr,width=10,height=1)
        self._set_speed_text.grid(row=0,column=8)


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

    def _init_map_frame(self,fr,map_ref,robot_ref):
        self._map_ui = MapUI(frame=fr,map_ref=map_ref)
        self._robotUI = RobotUI(robot=robot_ref,cells=self._map_ui.get_cells())

    def set_explore_coverage_limit(self):
        coverage = int(self._set_explore_coverage_limit_text.get("1.0",END))
        self._controller.set_explore_coverage_limit(coverage)

    def set_explore_speed(self):
        num_steps_per_sec = int(self._set_speed_text.get("1.0",END)[:-1])
        self._controller.set_explore_speed(num_steps_per_sec)

    def set_explore_time_limit(self):
        time_limit = int(self._set_explore_time_limit_text.get("1.0",END))
        self._controller.set_explore_time_limit(time_limit)

    def set_robot_pos(self):
        msg = self._set_robot_pos_text.get("1.0",END)[:-1]
        x,y=msg.split(",")
        self._controller.set_robot_pos(x,y)

    def load_map(self):
        map_file_path = self._load_map_text.get("1.0",END)[:-1]
        self._controller.load_map(map_file_path)

    def save_map(self):
        map_file_path = self._save_map_text.get("1.0",END)[:-1]
        self._controller.save_map(map_file_path)

    def update(self,data=None):
        if (data):
            self._cur_info.config(text=data)
        self._explore_time_remain_label.config(text="Remaining time: {}".format(self._controller.get_exploration_remaining_time()))
        self._explore_coverage_label.config(text="Coverage: {}".format(self._controller.get_cur_coverage()))


def main():
    window = Tk()
    app = ClientSimulationApp(root=window)
    window.title("Android")
    window.mainloop()

main()