import time
from thread import start_new_thread

from simulators.robot import RobotRef
from common.amap import *
from fsm import *
from algorithms.maze_explore import *
from algorithms.shortest_path import *

class CentralController(StateMachine):

    _cur_state = None
    _next_state = None

    _map_ref = None # internal map
    _robot = None
    _explore_algo = None
    _fastrun_algo = None

    FAST_RUN_COMMAND_DELAY = 0.5 # in second

    def set_next_state(self,state):
        print("Next state set to {}".format(str(state)))
        self._next_state = state

    def move_robot(self,action):
        self._robot.execute_command(action)

    def update_map(self,sensor_values):
        "update the map_ref according to received sensor readings"
        clear_pos_list,obstacle_pos_list = self._robot.sense_area(sensor_values)
        self._map_ref.set_cell_list(pos_list=clear_pos_list,value=MapRef.CLEAR)
        self._map_ref.set_cell_list(pos_list=obstacle_pos_list,value=MapRef.OBSTACLE)

    def get_next_exploration_move(self):
        return self._explore_algo.get_next_move()

    def is_map_fully_explored(self):
        "fully explored if the robot has explored the end zone and it has returned to start position"
        if (self._robot.get_position()==self._map_ref.get_start_zone_center_pos()):
            x,y=self._map_ref.get_end_zone_center_pos()
            if (self._map_ref.get_cell(x,y)==MapRef.CLEAR):
                return True
        return False

    def get_fast_run_commands(self):
        fastrun_algo = AStarShortestPathAlgo(map_ref=self._map_ref,target_pos=self._map_ref.get_end_zone_center_pos())
        return fastrun_algo.get_shortest_path(robot_pos=self._robot.get_position(),robot_ori=self._robot.get_orientation())

    def is_robot_at_destination(self):
        return self._robot.get_position()==self._map_ref.get_end_zone_center_pos()

    def reset(self):
        self._cur_state = ReadyState(machine=self)
        self._next_state = self._cur_state
        self._map_ref = MapRef()
        self._robot = RobotRef()
        self._explore_algo = MazeExploreAlgo(robot=self._robot,map_ref=self._map_ref)


    def __init__(self):
        self.reset()

    def update(self):
        pass

    def control_task(self,input_queue,command_out_queue,data_out_queues):
        "central control"
        # init robot
        while True:
            if (not input_queue.empty()):
                input_tuple = input_queue.get_nowait()
                if (not input_tuple): continue
                self._cur_state = self._next_state
                cmd_list,data_list = self._cur_state.process_input(input_tuple)
                if (cmd_list):
                    start_new_thread(self.enqueue_list,(command_out_queue,cmd_list,True,))
                if (data_list):
                    for q in data_out_queues:
                        start_new_thread(self.enqueue_list,(q,data_list,))

    def enqueue_list(self,q,list,allow_delay=False):
        if (len(list)==1):
            q.put_nowait(list[0])
        else:
            print("with sleep------")
            for item in list:
                q.put_nowait(item)
                if (allow_delay): time.sleep(self.FAST_RUN_COMMAND_DELAY)

    def load_map_from_file(self,file_name):
        self._map_ref.load_map_from_file(file_name)