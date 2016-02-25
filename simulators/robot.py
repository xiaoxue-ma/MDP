from common import *
from common.popattern import BasePublisher
from common.amap import *


class RobotSettings():
    BODY_COLOR = "red"
    HEAD_COLOR = "white"
    NOTHING_DETECTED = -1
    SENSORS = [
        {'pos': FRONT_LEFT, 'range': 4},  # front left
        {'pos': FRONT_RIGHT, 'range': 4},  # front right
        {'pos': FRONT, 'range': 4},  # front middle
        {'pos': LEFT, 'range': 3},  # left
        {'pos': RIGHT, 'range': 3},  # right
    ]


class RobotRef(RobotSettings, BasePublisher):
    """
    Encapsulate robot logic, act as publisher
    """
    _ori = None  # orientation
    _pos = None  # position (tuple)

    def __init__(self, ori=SOUTH, pos=(1, 1)):
        self._ori = ori
        self._pos = pos

    def refresh(self):
        self.notify()

    def set_orientation(self, ori):
        self._ori = ori
        self.notify()

    def set_position(self, pos_tuple):
        self._pos = pos_tuple
        self.notify()

    def turn_left(self):
        self.set_orientation(self._ori.to_left())

    def turn_right(self):
        self.set_orientation(self._ori.to_right())

    def move_forward(self):
        pos_change = self._ori.to_pos_change()
        self.set_position((self._pos[0] + pos_change[0], self._pos[1] + pos_change[1]))

    def execute_command(self, command):
        if (command == PMessage.M_TURN_RIGHT):
            self.turn_right()
        elif (command == PMessage.M_TURN_LEFT):
            self.turn_left()
        elif (command == PMessage.M_MOVE_FORWARD):
            self.move_forward()

    def get_sensor_readings(self, map_ref):
        """return a list of numbers"""
        readings = []
        for sensor in self.SENSORS:
            sensor_pos, sensor_ori = self.get_cur_sensor_state(rel_pos=sensor['pos'])
            readings.append(
                self._sense(map=map_ref, x=sensor_pos[0], y=sensor_pos[1], ori=sensor_ori, range=sensor['range']))
        return readings

    def get_cur_sensor_state(self, rel_pos):
        """return the actual sensor location and orientation"""
        abs_ori = rel_pos.get_actual_abs_ori(ref_front_ori=self._ori)
        position_delta = rel_pos.to_pos_change(rel_front_ori=self._ori)
        actual_position = (self._pos[0] + position_delta[0], self._pos[1] + position_delta[1])
        return actual_position, abs_ori

    def _sense(self, map, x, y, ori, range):
        """return int, the reading of one sensor"""
        dist = 0
        limit = range
        pos_delta = ori.to_pos_change()
        while (limit > 0):
            x += pos_delta[0]
            y += pos_delta[1]
            if map.is_out_of_arena(x, y) or map.get_cell(x, y) == MapRef.OBSTACLE:
                return dist
            dist += 1
            limit -= 1
        # no obstacle detected
        return -1

    def sense_area(self, sensor_values):
        """return list of position tuples for clear cells, and list of position tuples for blocked cells,regardless of the map size"""
        # NOTE: sensor values should correspond to Robot.SENSORS in sequence
        all_clear_list = []
        all_obstacle_list = []
        for i in range(len(sensor_values)):
            # get necessary info for update
            sensor_setting = self.SENSORS[i]
            sensor_range = sensor_setting['range']
            sensor_pos, sensor_ori = self.get_cur_sensor_state(rel_pos=sensor_setting['pos'])
            reading = sensor_values[i]
            pos_change = sensor_ori.to_pos_change()
            if reading == self.NOTHING_DETECTED:
                x_min, x_max = min(sensor_pos[0], sensor_pos[0] + pos_change[0] * sensor_range), max(sensor_pos[0],
                                                                                                     sensor_pos[0] +
                                                                                                     pos_change[
                                                                                                         0] * sensor_range)
                y_min, y_max = min(sensor_pos[1], sensor_pos[1] + pos_change[1] * sensor_range), max(sensor_pos[1],
                                                                                                     sensor_pos[1] +
                                                                                                     pos_change[
                                                                                                         1] * sensor_range)
                obstacle_list = []
            else:
                x_min, x_max = min(sensor_pos[0], sensor_pos[0] + pos_change[0] * reading), max(sensor_pos[0],
                                                                                                sensor_pos[0] +
                                                                                                pos_change[0] * (
                                                                                                    reading))
                y_min, y_max = min(sensor_pos[1], sensor_pos[1] + pos_change[1] * reading), max(sensor_pos[1],
                                                                                                sensor_pos[1] +
                                                                                                pos_change[1] * (
                                                                                                    reading))
                obstacle_list = [
                    (sensor_pos[0] + pos_change[0] * (reading + 1), sensor_pos[1] + pos_change[1] * (reading + 1))]

            clear_list = [
                (x, y) for x in range(x_min, x_max + 1)
                for y in range(y_min, y_max + 1) if x >= 0 and y >= 0
            ]
            all_clear_list.extend(clear_list)
            all_obstacle_list.extend(obstacle_list)

        return all_clear_list, all_obstacle_list


    def get_orientation(self):
        return self._ori

    def get_position(self):
        return self._pos


class RobotUI(RobotSettings, BaseObserver):
    """
    UI class for Robot
    """

    _cells = []  # 2d list of Button objects to paint on
    _robot = None  # Robot to attach to

    def __init__(self, cells, robot):
        """register myself as a listener for robot"""
        self._robot = robot
        self._cells = cells
        robot.add_change_listener(self)

    def paint_robot(self):
        """paint the robot shape on the cells given"""
        head_pos_dict = {NORTH.get_value(): (0, -1), SOUTH.get_value(): (0, 1), EAST.get_value(): (1, 0),
                         WEST.get_value(): (-1, 0)}
        head_pos = head_pos_dict[self._robot.get_orientation().get_value()]
        for i in range(-1, 2):  # horizontal
            for j in range(-1, 2):
                x, y = self._robot.get_position()[0] + i, self._robot.get_position()[1] + j
                if (i, j) == head_pos:
                    self._cells[y][x].config(highlightbackground=self.HEAD_COLOR)
                else:
                    self._cells[y][x].config(highlightbackground=self.BODY_COLOR)

    def update(self):
        self.paint_robot()