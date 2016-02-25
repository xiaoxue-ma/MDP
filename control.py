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
    _cur_state = None
    _next_state = None

    _map_ref = None  # internal map
    _robot = None
    _explore_algo = None
    _fastrun_algo = None

    _input_q = None  # input queue
    _cmd_out_q = None
    _data_out_qs = None  # list of queue

    _explore_time_limit = None  # integer
    _explore_coverage = None  # integer

    FAST_RUN_COMMAND_DELAY = 0.5  # in second

    def set_next_state(self, state):
        print("Next state set to {}".format(str(state)))
        for q in self._data_out_qs:
            self._enqueue_list(q=q, list=[PMessage(type=PMessage.T_STATE_CHANGE, msg=str(state))])
        self._next_state = state

    def update_remaining_explore_time(self, t):
        print("Exploration remaining time: {}".format(t))
        for q in self._data_out_qs:
            self._enqueue_list(q=q, list=[PMessage(type=PMessage.T_EXPLORE_REMAINING_TIME, msg=t)])

    def move_robot(self, action):
        self._robot.execute_command(action)

    def update_map(self, sensor_values):
        "update the map_ref according to received sensor readings"
        clear_pos_list, obstacle_pos_list = self._robot.sense_area(sensor_values)
        self._map_ref.set_cell_list(pos_list=clear_pos_list, value=MapRef.CLEAR)
        self._map_ref.set_cell_list(pos_list=obstacle_pos_list, value=MapRef.OBSTACLE)

    def get_next_exploration_move(self):
        return self._explore_algo.get_next_move()

    def is_map_fully_explored(self):
        "fully explored if the robot has explored the end zone and it has returned to start position"
        if (self._robot.get_position() == self._map_ref.get_start_zone_center_pos()):
            x, y = self._map_ref.get_end_zone_center_pos()
            if (self._map_ref.get_cell(x, y) == MapRef.CLEAR):
                return True
        return False

    def get_fast_run_commands(self):
        fastrun_algo = AStarShortestPathAlgo(map_ref=self._map_ref, target_pos=self._map_ref.get_end_zone_center_pos())
        result, time_taken = timed_call(fastrun_algo.get_shortest_path, robot_pos=self._robot.get_position(),
                                        robot_ori=self._robot.get_orientation())
        print("Fast run calculation takes {}".format(time_taken))
        return result

    def is_robot_at_destination(self):
        return self._robot.get_position() == self._map_ref.get_end_zone_center_pos()

    def set_exploration_time_limit(self, time_limit):
        self._explore_time_limit = int(time_limit)

    def set_exploration_coverage(self, coverage_percent):  # coverage limit
        self._explore_coverage = int(coverage_percent)

    def get_exploration_time_limit(self):
        return self._explore_time_limit

    def get_exploration_coverage_limit(self):
        return self._explore_coverage

    def get_current_exploration_coverage(self):
        return 100 - self._map_ref.get_unknown_percentage()

    def load_map_from_file(self, filename):
        self._map_ref.load_map_from_file(filename)

    def reset(self):
        self._cur_state = ReadyState(machine=self)
        self._next_state = self._cur_state
        self._map_ref = MapRef()
        self._robot = RobotRef()
        self._explore_algo = MazeExploreAlgo(robot=self._robot, map_ref=self._map_ref)


    def __init__(self, input_q, cmd_out_q, data_out_qs):
        self._input_q = input_q
        self._cmd_out_q = cmd_out_q
        self._data_out_qs = data_out_qs
        self.reset()

    def update(self):
        pass

    def control_task(self):
        "central control"
        # init robot
        while True:
            if not self._input_q.empty():
                input_tuple = self._input_q.get_nowait()
                if not input_tuple: continue
                self._cur_state = self._next_state
                cmd_list, data_list = self._cur_state.process_input(input_tuple)
                if cmd_list:
                    self._enqueue_list(self._cmd_out_q, cmd_list, True)
                if data_list:
                    for q in self._data_out_qs:
                        self._enqueue_list(q, data_list)

    def _enqueue_list(self, q, list, allow_delay=False):
        "enqueue list items on another thread"
        start_new_thread(self._enqueue_list_internal, (q, list, allow_delay,))

    def _enqueue_list_internal(self, q, list, allow_delay=False):
        "thread task"
        if len(list) == 1:
            q.put_nowait(list[0])
        else:
            for item in list:
                q.put_nowait(item)
                if allow_delay: time.sleep(self.FAST_RUN_COMMAND_DELAY)

    def load_map_from_file(self, file_name):
        self._map_ref.load_map_from_file(file_name)