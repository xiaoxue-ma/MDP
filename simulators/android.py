"""
test android client side
"""

from Tkinter import *
import socket
from thread import start_new_thread
import time

from common.pmessage import PMessage
from common.popattern import BaseObserver
from algorithms.maze_explore import MazeExploreAlgo
from algorithms.shortest_path import AStarShortestPathAlgo
from common.amap import *
from simulators.robot import *


class ClientSimulationApp():

    _text = None
    _mv_btn = None # button move forward
    _tl_btn = None # turn left
    _tr_btn = None # turn right
    _explore_btn = None
    _fastrun_btn = None # start fastest running
    _jump_explore_btn = None
    _sock = None # socket
    _explore_algo = None

    _map_ui = None
    _map_ref = [] #internal 2D representation of map
    _robot = None

    _connection = None # connection to client

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
        self._explore_btn = Button(master=root,text="explore",command=self.start_exploration)
        self._explore_btn.grid(row=5,column=0)
        #TODO: remove this in production
        self._jump_explore_btn = Button(master=root,text="jump explore",command=self.jump_explore)
        self._jump_explore_btn.grid(row=6,column=0)

        # init map
        self._map_ref = MapRef()
        self._map_frame = Frame(master=root)
        self._map_ui = MapUI(frame=self._map_frame,map_ref=self._map_ref)
        self._map_frame.grid(row=7,column=0)
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
        start_new_thread(self.start_server,())

    def start_fast_run(self):
        # compute run commands
        self.send_command(PMessage.M_START_FASTRUN)

    #TODO: remove this in production
    def jump_explore(self):
        self._map_ref.load_map_from_file("D:/map.txt")
        self.send_command(PMessage.M_JUMP_EXPLORE)

    def start_exploration(self):
        self.send_command(PMessage.M_START_EXPLORE)

    def send_command_list(self,cmd_list):
        for cmd in cmd_list:
            self.send_command(cmd)
            time.sleep(1)

    def send_command(self,command):
        if (not self._connection):
            raise Exception("socket not ready")
        self.send_data(con=self._connection,type=PMessage.T_COMMAND,
                       data = command)
        self.show_status("Sent command : " + str(command))

    def move_forward(self):
        self.send_command(PMessage.M_MOVE_FORWARD)

    def turn_left(self):
        self.send_command(PMessage.M_TURN_LEFT)

    def turn_right(self):
        self.send_command(PMessage.M_TURN_RIGHT)

    def start_server(self):
        # set up client socket
        time.sleep(1)
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        server_address = (MOCK_SERVER_ADDR,ANDROID_SERVER_PORT)
        sock.bind(server_address)
        self.show_status("server started...")
        # listening for connections
        sock.listen(1)
        connection,client_addr = sock.accept()
        self._connection = connection
        self.show_status("accept client: " + str(client_addr))
        self.serve_connection(connection)

    def serve_connection(self,con):
        while True:
            data =con.recv(1024)
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
        msg = PMessage(type=type,msg=data)
        con.sendall(str(msg))


def main():
    window = Tk()
    app = ClientSimulationApp(root=window)
    window.title("Android")
    window.mainloop()

main()