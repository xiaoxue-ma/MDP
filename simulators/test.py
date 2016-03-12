"""
test client side
"""

import socket
from thread import start_new_thread
import time

from algorithms.maze_explore import MazeExploreAlgo
from algorithms.shortest_path import AStarShortestPathAlgo
from common.robot import *


class ClientSimulationApp():

    _text = None
    _mv_btn = None # button move forward
    _tl_btn = None # turn left
    _tr_btn = None # turn right
    _fastrun_btn = None # start fastest running
    _sock = None # socket
    _explore_algo = None

    _map_ui = None
    _map_ref = None #internal 2D representation of map
    _robot = None

    def __init__(self,root):
        self._text = Text(master=root,height=10)
        self._text.grid(row=0,column=0)
        self._mv_btn = Button(master=root,text="move forward",command=self.move_forward)
        self._mv_btn.grid(row=1,column=0)
        self._tl_btn = Button(master=root,text="turn left",command=self.turn_left)
        self._tl_btn.grid(row=2,column=0)
        self._tr_btn = Button(master=root,text="turn right",command=self.turn_right)
        self._tr_btn.grid(row=3,column=0)
        self._fastrun_btn = Button(master=root,text="fast run",command=self.start_fast_run)
        self._fastrun_btn.grid(row=4,column=0)
        # init map
        self._map_ref = MapRef()
        self._map_frame = Frame(master=root)
        self._map_ui = MapUI(frame=self._map_frame,map_ref=self._map_ref)
        self._map_frame.grid(row=5,column=0)
        self._map_ref.refresh()
        # init robot
        self._robot = RobotRef()
        self._robotUI = RobotUI(robot=self._robot,cells=self._map_ui.get_cells())
        self._robot.refresh()
        # init algo
        self._explore_algo = MazeExploreAlgo(robot=self._robot,map_ref=self._map_ref)

        # start server
        start_new_thread(self.start_client,())

    def update(self):
        self._robot.paint_robot(cells=self._map_ui.get_cells())

    def start_fast_run(self):
        # compute run commands
        algo = AStarShortestPathAlgo(map_ref=self._map_ref,target_pos=(18,13))
        cmd_list = algo.get_shortest_path(robot_pos=self._robot.get_position(),robot_ori=self._robot.get_orientation())
        self.show_status(msg=str(cmd_list))
        # set up timer to send one by one
        start_new_thread(self.send_command_list,(cmd_list,))

    def send_command_list(self,cmd_list):
        for cmd in cmd_list:
            self.send_command(cmd)
            time.sleep(1)

    def send_command(self,command):
        if (not self._sock):
            raise Exception("socket not ready")
        self._sock.sendall(command)
        self.show_status("Sent command : " + str(command))

    def move_forward(self):
        self.send_command(PMessage.M_MOVE_FORWARD)

    def turn_left(self):
        self.send_command(PMessage.M_TURN_LEFT)

    def turn_right(self):
        self.send_command(PMessage.M_TURN_RIGHT)

    def start_client(self):
        # set up client socket
        time.sleep(1)
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self._sock = sock
        server_address = (MOCK_SERVER_ADDR,ARDUINO_SERVER_PORT)
        sock.connect(server_address)
        self.show_status("server connected...")
        # listening for connections
        while(True):
            data = sock.recv(1024)
            if (data):
                self.show_status("received data: " + str(data))
                reply = self.process_data(data)
                sock.sendall(reply)

    def process_data(self,recv_data):
        "update the map according to sensor data and return reply msg"
        sensor_values = [int(i) for i in recv_data.split(",")]
        self.update_map(sensor_values)
        # update robot
        command = self._explore_algo.get_next_move()
        self.show_status("determined move: " + command)
        self._robot.execute_command(command)
        # reply
        return command

    def update_map(self,sensor_values):
        "update the map_ref and also the gui"
        clear_pos_list,obstacle_pos_list = self._robot.sense_area(sensor_values)
        self._map_ref.set_cell_list(pos_list=clear_pos_list,value=MapRef.CLEAR)
        self._map_ref.set_cell_list(pos_list=obstacle_pos_list,value=MapRef.OBSTACLE)

    def show_status(self,msg):
        self._text.insert(END,msg+"\n")


def main():
    window = Tk()
    app = ClientSimulationApp(root=window)
    window.mainloop()

main()