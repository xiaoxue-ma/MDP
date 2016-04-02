from __future__ import print_function
import Queue


class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Map:
    width = 15
    height = 20

    def __init__(self):
        self.grid = [[-1 for x in range(15)] for y in range(20)]
        self.grid[19][0] = 0
        self.grid[18][0] = 0
        self.grid[17][0] = 0
        self.grid[19][1] = 0
        self.grid[18][1] = 0
        self.grid[17][1] = 0
        self.grid[19][2] = 0
        self.grid[18][2] = 0
        self.grid[17][2] = 0
        self.grid[0][12] = 0
        self.grid[0][13] = 0
        self.grid[0][14] = 0
        self.grid[1][12] = 0
        self.grid[1][13] = 0
        self.grid[1][14] = 0
        self.grid[2][12] = 0
        self.grid[2][13] = 0
        self.grid[2][14] = 0

    def print_map(self):
        for y in range(20):
            for x in range(15):
                print (self.grid[y][x],end='')
            print ('')

    def update_map(self, x, y, value):
        if (y >= 0 and y < 20 and x >= 0 and x < 15 and self.grid[y][x] < 0):
            self.grid[y][x] = value
            return "{},{},{}".format(x,y,value)
        else:
            return ""


class Algo:
    def __init__(self):
        self.x = 1
        self.y = 18
        self.Range = 1
        self.direction = '3'
        self.map = Map()
        self.x_goal = 13
        self.y_goal = 1
        self.x_start = 1
        self.y_start = 18
        self.last_dir = '3'
        self.explore_start = False
        self.explore_done = False
        self.fast_start = False
        self.fast_done = False
        self.enter_goal = False
        self.save_command = False
        self.write_command = False
        self.commands=Queue.Queue(maxsize=0)

    def turn_left(self):
        if self.direction == '1':
            self.direction = '7'

        elif self.direction == '5':
            self.direction = '3'

        elif self.direction == '3':
            self.direction = '1'

        elif self.direction == '7':
            self.direction = '5'
        self.last_dir = self.direction
        if not self.enter_goal:
            self.commands.put_nowait("L")

    def turn_right(self):
        if self.direction == '1':
            self.direction = '3'

        elif self.direction == '5':
            self.direction = '7'

        elif self.direction == '3':
            self.direction = '5'

        elif self.direction == '7':
            self.direction = '1'
        self.last_dir = self.direction
        if not self.enter_goal:
            self.commands.put_nowait("R")

    def move_forward(self):
        if self.direction == '1':
            self.y -= 1

        elif self.direction == '5':
            self.y += 1

        elif self.direction == '3':
            self.x += 1

        elif self.direction == '7':
            self.x -= 1

        if self.x == self.x_goal and self.y == self.y_goal:
            self.enter_goal = True
        if not self.enter_goal:
            self.commands.put_nowait("M")

    def turn_back(self):
        if self.direction == '1':
            self.direction = '5'

        elif self.direction == '5':
            self.direction = '1'

        elif self.direction == '3':
            self.direction = '7'

        elif self.direction == '7':
            self.direction = '3'
        self.last_dir = self.direction
        if not self.enter_goal:
            self.commands.put_nowait("B")

    def in_start_zone(self):
        if self.x == self.x_start and self.y == self.y_start:
            return True
        else:
            return False

    def is_end_zone(self):
        if self.x == self.x_goal and self.y == self.y_goal:
            return True
        else:
            return False

    def explore(self):
        if not self.explore_start:
            self.explore_start = True
            self.enter_goal = False
        self.save_command = True
        self.write_command = False
        return "SE"

    def fast(self):
        self.save_command = False
        self.write_command = True
        self.enter_goal = False

    def update_map(self, msg):
        readings = msg.split(',')
        print ("updating map", end='')
        print(msg)
        result = ""
        if self.last_dir == '1':
            if readings[0] == '0':
                tmp = self.map.update_map(-1 + self.x, self.y - 2, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[0] == '1':
                tmp = self.map.update_map(-1 + self.x, self.y - 2, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(-1 + self.x, self.y - 3, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[0] == '-1':
                tmp = self.map.update_map(-1 + self.x, self.y - 2, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(-1 + self.x, self.y - 3, 0)
                if tmp != "":
                    result = result + tmp + "|"

            if readings[1] == '0':
                tmp = self.map.update_map(1 + self.x, self.y - 2, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[1] == '1':
                tmp = self.map.update_map(1 + self.x, self.y - 2, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(1 + self.x, self.y - 3, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[1] == '-1':
                tmp = self.map.update_map(1 + self.x, self.y - 2, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(1 + self.x, self.y - 3, 0)
                if tmp != "":
                    result = result + tmp + "|"

            if readings[2] == '0':
                tmp = self.map.update_map(self.x, self.y - 2, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[2] == '1':
                tmp = self.map.update_map(self.x, self.y - 2, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x, self.y - 3, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[2] == '-1':
                tmp = self.map.update_map(self.x, self.y - 2, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x, self.y - 3, 0)
                if tmp != "":
                    result = result + tmp + "|"

            if readings[3] == '0':
                tmp = self.map.update_map(self.x - 2, self.y + 1, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[3] == '1':
                tmp = self.map.update_map(self.x - 2, self.y + 1, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x - 3, self.y + 1, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[3] == '-1':
                tmp = self.map.update_map(self.x - 2, self.y + 1, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x - 3, self.y + 1, 0)
                if tmp != "":
                    result = result + tmp + "|"

            if readings[4] == '0':
                tmp = self.map.update_map(self.x + 2, self.y - 1, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[4] == '1':
                tmp = self.map.update_map(self.x + 2, self.y - 1, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x + 3, self.y - 1, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[4] == '-1':
                tmp = self.map.update_map(self.x + 2, self.y - 1, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x + 3, self.y - 1, 0)
                if tmp != "":
                    result = result + tmp + "|"

            if readings[5] == '0':
                tmp = self.map.update_map(self.x + 2, self.y + 1, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[5] == '1':
                tmp = self.map.update_map(self.x + 2, self.y + 1, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x + 3, self.y + 1, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[5] == '-1':
                tmp = self.map.update_map(self.x + 2, self.y + 1, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x + 3, self.y + 1, 0)
                if tmp != "":
                    result = result + tmp + "|"

        elif self.last_dir == '3':
            if readings[0] == '0':
                tmp = self.map.update_map(self.x + 2, self.y - 1, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[0] == '1':
                tmp = self.map.update_map(self.x + 2, self.y - 1, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x + 3, self.y - 1, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[0] == '-1':
                tmp = self.map.update_map(self.x + 2, self.y - 1, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x + 3, self.y - 1, 0)
                if tmp != "":
                    result = result + tmp + "|"

            if readings[1] == '0':
                tmp = self.map.update_map(self.x + 2, self.y + 1, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[1] == '1':
                tmp = self.map.update_map(self.x + 2, self.y + 1, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x + 3, self.y + 1, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[1] == '-1':
                tmp = self.map.update_map(self.x + 2, self.y + 1, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x + 3, self.y + 1, 0)
                if tmp != "":
                    result = result + tmp + "|"

            if readings[2] == '0':
                tmp = self.map.update_map(self.x + 2, self.y, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[2] == '1':
                tmp = self.map.update_map(self.x + 2, self.y, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x + 3, self.y, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[2] == '-1':
                tmp = self.map.update_map(self.x + 2, self.y, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x + 3, self.y, 0)
                if tmp != "":
                    result = result + tmp + "|"

            if readings[3] == '0':
                tmp = self.map.update_map(-1 + self.x, self.y - 2, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[3] == '1':
                tmp = self.map.update_map(-1 + self.x, self.y - 2, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(-1 + self.x, self.y - 3, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[3] == '-1':
                tmp = self.map.update_map(-1 + self.x, self.y - 2, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(-1 + self.x, self.y - 3, 0)
                if tmp != "":
                    result = result + tmp + "|"

            if readings[4] == '0':
                tmp = self.map.update_map(1 + self.x, self.y + 2, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[4] == '1':
                tmp = self.map.update_map(1 + self.x, self.y + 2, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(1 + self.x, self.y + 3, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[4] == '-1':
                tmp = self.map.update_map(1 + self.x, self.y + 2, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(1 + self.x, self.y + 3, 0)
                if tmp != "":
                    result = result + tmp + "|"

            if readings[5] == '0':
                tmp = self.map.update_map(-1 + self.x, self.y + 2, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[5] == '1':
                tmp = self.map.update_map(-1 + self.x, self.y + 2, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(-1 + self.x, self.y + 3, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[5] == '-1':
                tmp = self.map.update_map(-1 + self.x, self.y + 2, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(-1 + self.x, self.y + 3, 0)
                if tmp != "":
                    result = result + tmp + "|"

        elif self.last_dir == '5':
            if readings[0] == '0':
                tmp = self.map.update_map(1 + self.x, self.y + 2, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[0] == '1':
                tmp = self.map.update_map(1 + self.x, self.y + 2, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(1 + self.x, self.y + 3, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[0] == '-1':
                tmp = self.map.update_map(1 + self.x, self.y + 2, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(1 + self.x, self.y + 3, 0)
                if tmp != "":
                    result = result + tmp + "|"

            if readings[1] == '0':
                tmp = self.map.update_map(-1 + self.x, self.y + 2, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[1] == '1':
                tmp = self.map.update_map(-1 + self.x, self.y + 2, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(-1 + self.x, self.y + 3, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[1] == '-1':
                tmp = self.map.update_map(-1 + self.x, self.y + 2, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(-1 + self.x, self.y + 3, 0)
                if tmp != "":
                    result = result + tmp + "|"

            if readings[2] == '0':
                tmp = self.map.update_map(self.x, self.y + 2, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[2] == '1':
                tmp = self.map.update_map(self.x, self.y + 2, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x, self.y + 3, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[2] == '-1':
                tmp = self.map.update_map(self.x, self.y + 2, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x, self.y + 3, 0)
                if tmp != "":
                    result = result + tmp + "|"

            if readings[3] == '0':
                tmp = self.map.update_map(self.x + 2, self.y - 1, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[3] == '1':
                tmp = self.map.update_map(self.x + 2, self.y - 1, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x + 3, self.y - 1, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[3] == '-1':
                tmp = self.map.update_map(self.x + 2, self.y - 1, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x + 3, self.y - 1, 0)
                if tmp != "":
                    result = result + tmp + "|"

            if readings[4] == '0':
                tmp = self.map.update_map(self.x - 2, self.y + 1, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[4] == '1':
                tmp = self.map.update_map(self.x - 2, self.y + 1, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x - 3, self.y + 1, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[4] == '-1':
                tmp = self.map.update_map(self.x - 2, self.y + 1, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x - 3, self.y + 1, 0)
                if tmp != "":
                    result = result + tmp + "|"

            if readings[5] == '0':
                tmp = self.map.update_map(self.x - 2, self.y - 1, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[5] == '1':
                tmp = self.map.update_map(self.x - 2, self.y - 1, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x - 3, self.y - 1, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[5] == '-1':
                tmp = self.map.update_map(self.x - 2, self.y - 1, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x - 3, self.y - 1, 0)
                if tmp != "":
                    result = result + tmp + "|"

        elif self.last_dir == '7':
            if readings[0] == '0':
                tmp = self.map.update_map(self.x - 2, self.y + 1, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[0] == '1':
                tmp = self.map.update_map(self.x - 2, self.y + 1, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x - 3, self.y + 1, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[0] == '-1':
                tmp = self.map.update_map(self.x - 2, self.y + 1, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x - 3, self.y + 1, 0)
                if tmp != "":
                    result = result + tmp + "|"

            if readings[1] == '0':
                tmp = self.map.update_map(self.x - 2, self.y - 1, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[1] == '1':
                tmp = self.map.update_map(self.x - 2, self.y - 1, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x - 3, self.y - 1, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[1] == '-1':
                tmp = self.map.update_map(self.x - 2, self.y - 1, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x - 3, self.y - 1, 0)
                if tmp != "":
                    result = result + tmp + "|"

            if readings[2] == '0':
                tmp = self.map.update_map(self.x - 2, self.y, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[2] == '1':
                tmp = self.map.update_map(self.x - 2, self.y, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x - 3, self.y, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[2] == '-1':
                tmp = self.map.update_map(self.x - 2, self.y, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(self.x - 3, self.y, 0)
                if tmp != "":
                    result = result + tmp + "|"

            if readings[3] == '0':
                tmp = self.map.update_map(1 + self.x, self.y + 2, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[3] == '1':
                tmp = self.map.update_map(1 + self.x, self.y + 2, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(1 + self.x, self.y + 3, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[3] == '-1':
                tmp = self.map.update_map(1 + self.x, self.y + 2, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(1 + self.x, self.y + 3, 0)
                if tmp != "":
                    result = result + tmp + "|"

            if readings[4] == '0':
                tmp = self.map.update_map(-1 + self.x, self.y - 2, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[4] == '1':
                tmp = self.map.update_map(-1 + self.x, self.y - 2, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(-1 + self.x, self.y - 3, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[4] == '-1':
                tmp = self.map.update_map(-1 + self.x, self.y - 2, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(-1 + self.x, self.y - 3, 0)
                if tmp != "":
                    result = result + tmp + "|"

            if readings[5] == '0':
                tmp = self.map.update_map(1 + self.x, self.y - 2, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[5] == '1':
                tmp = self.map.update_map(1 + self.x, self.y - 2, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(1 + self.x, self.y - 3, 1)
                if tmp != "":
                    result = result + tmp + "|"
            elif readings[5] == '-1':
                tmp = self.map.update_map(1 + self.x, self.y - 2, 0)
                if tmp != "":
                    result = result + tmp + "|"
                tmp = self.map.update_map(1 + self.x, self.y - 3, 0)
                if tmp != "":
                    result = result + tmp + "|"

        if len(result) > 5:
            return result[:-1]






