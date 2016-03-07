from common import *
from common.popattern import BasePublisher
from copy import copy
from common.amap import *

class RobotSettings():
    BODY_COLOR = "red"
    HEAD_COLOR = "white"
    NOTHING_DETECTED = -1
    SENSORS = [
        {'pos':FRONT_LEFT,'range':2},# front left
        {'pos':FRONT_RIGHT,'range':2}, # front right
        {'pos':FRONT,'range':2}, # front middle
        {'pos':LEFT,'range':4}, # left
        {'pos':RIGHT,'range':2}, # right
    ]

class RobotRef(RobotSettings,BasePublisher):
    """
    Encapsulate robot logic, act as publisher
    """
    _ori = None # orientation
    _pos = None # position (tuple)

    def __init__(self,ori=EAST,pos=(1,18)):
        self.reset(ori,pos)

    def reset(self,ori=EAST,pos=(1,18)):
        self._ori = ori
        self._pos = pos
        self.notify()

    def refresh(self):
        self.notify()

    def set_orientation(self,ori):
        self._ori = ori
        self.notify()

    def set_position(self,pos_tuple):
        self._pos = pos_tuple
        self.notify()

    def turn_left(self):
        self.set_orientation(self._ori.to_left())

    def turn_right(self):
        self.set_orientation(self._ori.to_right())

    def turn_back(self):
        self.set_orientation(self._ori.to_back())

    def move_forward(self):
        pos_change = self._ori.to_pos_change()
        self.set_position((self._pos[0]+pos_change[0],self._pos[1]+pos_change[1]))

    def execute_command(self,command):
        if (command==PMessage.M_TURN_RIGHT): self.turn_right()
        elif (command==PMessage.M_TURN_LEFT): self.turn_left()
        elif(command==PMessage.M_MOVE_FORWARD): self.move_forward()
        elif(command==PMessage.M_TURN_BACK): self.turn_back()
        else:print("Command {} is not a valid command for robot".format(command))

    def get_sensor_readings(self,map_ref):
        "return a list of numbers"
        readings = []
        for sensor in self.SENSORS:
            sensor_pos,sensor_ori = self.get_cur_sensor_state(rel_pos=sensor['pos'])
            readings.append(self._sense(map=map_ref,x=sensor_pos[0],y=sensor_pos[1],ori=sensor_ori,range=sensor['range']))
        return readings

    def get_cur_sensor_state(self,rel_pos):
        "return the actual sensor location and orientation"
        abs_ori = rel_pos.get_actual_abs_ori(ref_front_ori=self._ori)
        position_delta = rel_pos.to_pos_change(rel_front_ori=self._ori)
        actual_position = (self._pos[0] + position_delta[0], self._pos[1] + position_delta[1])
        return actual_position,abs_ori

    def _sense(self,map,x,y,ori,range):
        "return int, the reading of one sensor"
        dist = 0
        limit = range
        pos_delta = ori.to_pos_change()
        while (limit>0):
            x += pos_delta[0]
            y += pos_delta[1]
            if (map.is_out_of_arena(x,y) or map.get_cell(x,y)==MapRef.OBSTACLE):
                return dist
            dist +=1
            limit -=1
        # no obstacle detected
        return -1

    def sense_area(self,sensor_values):
        "return list of position tuples for clear cells, and list of position tuples for blocked cells,regardless of the map size"
        # NOTE: sensor values should correspond to Robot.SENSORS in sequence
        all_clear_list = []
        all_obstacle_list = []
        for i in range(len(sensor_values)):
            # get necessary info for update
            sensor_setting = self.SENSORS[i]
            sensor_range = sensor_setting['range']
            sensor_pos,sensor_ori = self.get_cur_sensor_state(rel_pos=sensor_setting['pos'])
            reading = sensor_values[i]
            pos_change = sensor_ori.to_pos_change()
            if (reading==self.NOTHING_DETECTED):
                x_min,x_max = min(sensor_pos[0],sensor_pos[0]+pos_change[0]*sensor_range),max(sensor_pos[0],sensor_pos[0]+pos_change[0]*sensor_range)
                y_min,y_max = min(sensor_pos[1],sensor_pos[1]+pos_change[1]*sensor_range),max(sensor_pos[1],sensor_pos[1]+pos_change[1]*sensor_range)
                obstacle_list = []
            else:
                x_min,x_max = min(sensor_pos[0],sensor_pos[0]+pos_change[0]*(reading)),max(sensor_pos[0],sensor_pos[0]+pos_change[0]*(reading))
                y_min,y_max = min(sensor_pos[1],sensor_pos[1]+pos_change[1]*(reading)),max(sensor_pos[1],sensor_pos[1]+pos_change[1]*(reading))
                obstacle_list = [(sensor_pos[0]+pos_change[0]*(reading+1),sensor_pos[1]+pos_change[1]*(reading+1))]

            clear_list = [
                (x,y) for x in range(x_min,x_max+1)
                for y in range(y_min,y_max+1) if x>=0 and y>=0
            ]
            all_clear_list.extend(clear_list)
            all_obstacle_list.extend(obstacle_list)

        return all_clear_list,all_obstacle_list

    def get_action_utility_points(self,action,map_ref):
        "return the number of grids the robot can explore should it take the given action"
        num_sensors = len(self.SENSORS)
        robot_copy = copy(self)
        robot_copy.execute_command(action)
        robot_copy.execute_command(PMessage.M_MOVE_FORWARD)
        clear_ls,obstacle_ls = robot_copy.sense_area([self.NOTHING_DETECTED]*num_sensors)
        utility_point = 0
        for x,y in clear_ls:
            if (not map_ref.is_out_of_arena(x,y) and map_ref.get_cell(x,y)==map_ref.UNKNOWN):
                utility_point += 1
        return utility_point

    def get_orientation(self):
        return self._ori

    def get_position(self):
        "return the centre position of the robot"
        return self._pos

    def get_occupied_postions(self):
        "return a list of pos that the robot occupies, hard coded for 3*3"
        x,y=self._pos
        return [(x+i,y+j) for i in range(-1,2) for j in range(-1,2)]

    def get_head_position(self):
        return sum_coordinate(self._pos,self._ori.to_pos_change())

class RobotUI(RobotSettings,BaseObserver):
    """
    UI class for Robot
    """

    _cells = [] # 2d list of Button objects to paint on
    _robot = None # Robot to attach to

    def __init__(self,cells,robot):
        "register myself as a listener for robot"
        self._robot = robot
        self._cells = cells
        robot.add_change_listener(self)
        self.update()

    def paint_robot(self):
        "paint the robot shape on the cells given"
        body_pos_ls = self._robot.get_occupied_postions()
        head_pos = self._robot.get_head_position()
        for x,y in body_pos_ls:
            if ((x,y)==head_pos):
                self._cells[y][x].config(bg=self.HEAD_COLOR)
            else:
                self._cells[y][x].config(bg=self.BODY_COLOR)

    def update(self,data=None):
        self.paint_robot()