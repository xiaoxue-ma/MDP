import time
from thread import start_new_thread

from common.robot import RobotRef
from common.timer import timed_call
from fsm import *
from algorithms.maze_explore import *
from algorithms.shortest_path import *


class CentralController(StateMachine):
    """
    run control_task method to start running the controller
    """

    _map_ref = None # internal map
    _robot = None
    _explore_algo = None
    _fastrun_algo = None

    _input_q = None # input queue
    _cmd_out_q = None
    _data_out_qs = None # list of queue

    _explore_time_limit = None # integer
    _explore_coverage = None # integer

    _exploration_command_delay = 2

    FAST_RUN_COMMAND_DELAY = 2 # in second

    def control_task(self):
        "central control"
        # init robot
        while True:
            if (not self._input_q.empty()):
                input_tuple = self._input_q.get_nowait()
                if (not input_tuple): continue
                cmd_list,data_list = self._state.process_input(input_tuple)
                if (cmd_list):
                    self._enqueue_list(self._cmd_out_q,cmd_list,True)
                if (data_list):
                    for q in self._data_out_qs:
                        self._enqueue_list(q,data_list)

    # deprecated
    def set_exploration_command_delay(self,delay):
        self._exploration_command_delay=delay
        print("Exploration delay set to {} secs per step".format(delay))

    def set_next_state(self,state):
        print("Next state set to {}".format(str(state)))
        for q in self._data_out_qs:
            self._enqueue_list(q=q,list=[PMessage(type=PMessage.T_STATE_CHANGE,msg=str(state))])
        self._state = state

    def update_remaining_explore_time(self,t):
        print("Exploration remaining time: {}".format(t))
        for q in self._data_out_qs:
            self._enqueue_list(q=q,list=[PMessage(type=PMessage.T_EXPLORE_REMAINING_TIME,msg=t)])

    def move_robot(self,action):
        self._robot.execute_command(action)

    def update_map(self,sensor_values):
        "update the map_ref according to received sensor readings"
        clear_pos_list,obstacle_pos_list = self._robot.sense_area(sensor_values)
        self._map_ref.set_cell_list(pos_list=clear_pos_list,value=MapRef.CLEAR)
        self._map_ref.set_cell_list(pos_list=obstacle_pos_list,value=MapRef.OBSTACLE)
        return clear_pos_list,obstacle_pos_list

    def get_next_exploration_move(self):
        return self._explore_algo.get_next_move()

    def get_fast_run_commands(self):
        fastrun_algo = AStarShortestPathAlgo(map_ref=self._map_ref,target_pos=self._map_ref.get_end_zone_center_pos())
        result, time_taken = timed_call(fastrun_algo.get_shortest_path,robot_pos=self._robot.get_position(),robot_ori=self._robot.get_orientation())
        print("Fast run calculation takes {}".format(time_taken))
        return result

    def is_robot_at_destination(self):
        return self._robot.get_position()==self._map_ref.get_end_zone_center_pos()

    def is_robot_at_start(self):
        return self._robot.get_position()==self._map_ref.get_start_zone_center_pos()

    def set_exploration_time_limit(self,time_limit):
        self._explore_time_limit = int(time_limit)

    def set_exploration_coverage(self,coverage_percent): # coverage limit
        self._explore_coverage = int(coverage_percent)

    def get_exploration_time_limit(self):
        return self._explore_time_limit

    def get_exploration_coverage_limit(self):
        return self._explore_coverage

    def get_current_exploration_coverage(self):
        return 100 - self._map_ref.get_unknown_percentage()

    def get_exploration_command_delay(self):
        return self._exploration_command_delay

    def get_map_ref(self):
        return self._map_ref

    def get_robot_ref(self):
        return self._robot

    def load_map_from_file(self,filename):
        self._map_ref.load_map_from_file(filename)

    def set_robot_pos(self,pos):
        "pos should be a tuple"
        self._robot.set_position(pos)

    def reset(self):
        self._state = ReadyState(machine=self)
        self._map_ref = MapRef()
        self._robot = RobotRef()
        self._explore_algo = MazeExploreAlgo(robot=self._robot,map_ref=self._map_ref)
        self._explore_time_limit = None # integer
        self._explore_coverage = None

    def __init__(self,input_q,cmd_out_q,data_out_qs):
        self._input_q = input_q
        self._cmd_out_q = cmd_out_q
        self._data_out_qs = data_out_qs
        self.reset()

    def update(self):
        pass

    # allow delay is deprecated
    def _enqueue_list(self,q,list,allow_delay=False):
        "enqueue list items on another thread"
        start_new_thread(self._enqueue_list_internal,(q,list,allow_delay,))

    def _enqueue_list_internal(self,q,list,allow_delay=False):
        "thread task"
        for item in list:
            if (item):
                q.put_nowait(item)

    def get_robot_pos(self):
        return self._robot.get_position()

    def get_robot_ori(self):
        return self._robot.get_orientation()