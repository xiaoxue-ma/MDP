import os
import re
from Tkinter import *
from abc import ABCMeta,abstractmethod
from bitarray import bitarray

from common import *
from common.popattern import *

class MapSetting():
    # map settings
    DEFAULT_MAP_SIZE_X = 15
    DEFAULT_MAP_SIZE_Y = 20
    DEFAULT_START_POS = (1,18)
    DEFAULT_END_POS = (13,1)

    # possible values of the each cell
    CLEAR = 0
    OBSTACLE = 1
    UNKNOWN = 2
    START_ZONE = 3
    END_ZONE = 4

    DEFAULT_CELL_VALUE = UNKNOWN
    VALID_CELL_VALUES = [CLEAR,OBSTACLE,UNKNOWN,START_ZONE,END_ZONE]
    START_ZONE_INDICES = [(x,y) for x in range(3) for y in range(3)]
    # default directory to store map descriptors
    # see MapRef
    MAP_FILE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)),'simulators/mapfiles')

class BaseMapIOMixin():
    """
    class for loading and saving map to file
    """
    __metaclass__ = ABCMeta

    def _get_abs_file_name(self,filename):
        "convert to abs path if it's not"
        abs_path_pattern =re.compile('[A-Z]:/')
        if (abs_path_pattern.findall(filename)):
            return filename
        else:
            return os.path.join(MapSetting.MAP_FILE_DIR,filename)

    def load_map(self,filename):
        "return a 2D array representing the map"
        return self._load_map_file(self._get_abs_file_name(filename))

    @abstractmethod
    def _load_map_file(self,filename):
        "return a 2D array representing the map"
        return []

    def save_map(self,filename,td_array):
        "td_array is the internal map representation, return None, may raise IOException"
        self._save_map_file(self._get_abs_file_name(filename),td_array=td_array)

    @abstractmethod
    def _save_map_file(self,filename,td_array):
        "td_array is the internal map representation, return None, may raise IOException"
        pass


class TextMapIOMixin(BaseMapIOMixin):
    """
    Read and write map as text file
    """
    def _load_map_file(self,filename):
        ROW_LEN = 15
        with open(filename,"r") as f:
            content = f.read()
        ls = [int(i) for i in content if i.isdigit()]
        return [ls[15*i:15*(i+1)] for i in range(len(ls)/ROW_LEN)]

    def _save_map_file(self,filename,td_array):
        with open(filename,'w') as f:
            f.write(
                ''.join(str(td_array[y][x])
                        for y in range(len(td_array))
                        for x in range(len(td_array[0])))
            )

class BitMapIOMixin(BaseMapIOMixin):
    """
    Save map in binary format
    """
    bit_unknown = 0
    bit_explored = 1
    bit_clear = 0
    bit_obstacle = 1

    _is_top_down = False # whether the read/write the map from top to down

    def set_top_down(self,is_top_down):
        self._is_top_down = is_top_down

    def to_hex(self,x):
        "take in a bytes str and return a str in hex"
        return "".join("{:02X}".format(ord(c)) for c in x)

    def _load_map_file(self,filename):
        #TODO: so far this is hardcoded, only read 15*20 map
        with open(filename,"rb") as f:
            content = f.read()
        arr = bitarray()
        arr.frombytes(content)
        print("Map loaded: {}".format(self.to_hex(arr.tobytes())))
        explored = arr[2:302] # explored or unknown
        cleared = arr[304:] # cleared or obstacle
        # load into a 2d array
        ls = [[None for _ in range(15) ] for __ in range(20)]
        cleared_cur_index = 0
        for i in range(len(explored)):
            x = i%15
            y = i/15
            if (explored[i]==self.bit_unknown):
                ls[y][x] = MapSetting.UNKNOWN
            else: # explored
                if (cleared[cleared_cur_index]==self.bit_clear):
                    ls[y][x] = MapSetting.CLEAR
                else:#obstacle
                    ls[y][x] = MapSetting.OBSTACLE
                cleared_cur_index += 1
        if (any([True if ls[y][x]==None else False
                 for y in range(20) for x in range(15)])):
            raise Exception("The map data is not complete")
        if (not self._is_top_down):
            ls = list(reversed(ls))
        return ls

    def _save_map_file(self,filename,td_array):
        if (not self._is_top_down):
            td_array = list(reversed(td_array))
        explored_ls = [] # record explored or unknown
        cleared_ls = [] # record clear or obstacle
        explored_ls.extend([1,1]) # prefix
        for y in range(len(td_array)):
            for x in range(len(td_array[0])):
                if td_array[y][x]==MapSetting.UNKNOWN:
                    explored_ls.append(self.bit_unknown)
                else:# explored
                    explored_ls.append(self.bit_explored)
                    if (td_array[y][x]==MapSetting.OBSTACLE):
                        cleared_ls.append(self.bit_obstacle)
                    else:
                        cleared_ls.append(self.bit_clear)
        explored_ls.extend([1,1]) # postfix
        # concatenate the two lists
        result_ls = self._pad_zero_right(explored_ls+cleared_ls)
        arr = bitarray([result_ls[i]==1 for i in range(len(result_ls))])
        print("Map saved: {}".format(self.to_hex(arr.tobytes())))
        # write the binary string to file
        with open(filename,'wb') as f:
            f.write(arr.tobytes())

    def _pad_zero_right(self,ls):
        "pad zero to the list so that the length is a power of 2"
        import math
        power = int(
            math.ceil(math.log(len(ls),2))
        )
        num_zeros = 2**power - len(ls)
        ls.extend([0]*num_zeros)
        return ls

class MapRef(BitMapIOMixin,MapSetting,BasePublisher):
    """
    internal representation of the arena map
    """

    # map data
    _map_ref = [] # 2D matrix
    size_x = 0
    size_y = 0
    _start_zone_centre_pos = ()
    _end_zone_centre_pos = ()

    _listeners = [] # list of observers

    def __init__(self,x=None,y=None,default=None):
        self.reset(x,y,default)

    def reset(self,x=None,y=None,default=None):
        self._start_zone_centre_pos=self.DEFAULT_START_POS
        self._end_zone_centre_pos = self.DEFAULT_END_POS
        if (x and y and default):
            self._map_ref = [[default for _ in range(x)] for __ in range(y)]
        else:
            self._map_ref = [[self.DEFAULT_CELL_VALUE for _ in range(self.DEFAULT_MAP_SIZE_X)] for __ in range(self.DEFAULT_MAP_SIZE_Y)]
        # set start zone to be clear
        self._update_size()
        indexes = self.get_start_zone_indexes()
        self.set_cell_list(indexes,value=MapSetting.CLEAR)
        self.notify()

    def get_unknown_percentage(self):
        map_size = self.size_y * self.size_x
        num_unknown_cells = sum([1 for x in range(self.size_x) for y in range(self.size_y) if self.get_cell(x,y)==self.UNKNOWN])
        return int(100.0*num_unknown_cells/map_size)

    def refresh(self):
        self.notify()

    def get_cell(self,x,y):
        return self._map_ref[y][x]

    def set_cell(self,x,y,value,notify=True):
        self._map_ref[y][x] = value
        if (notify):
            self.notify()

    def set_cell_list(self,pos_list,value):
        "pos_list should be a list of (x,y)"
        for x,y in pos_list:
            if (not self.is_out_of_arena(x,y)):
                self.set_cell(x,y,value,notify=False)
        self.notify()

    def get_surrounding_pos(self,x,y):
        "return a list of positions that surround (x,y)"
        return [(x+i,y+j) for i in range(-1,2) for j in range(-1,2) if (i!=0 or j!=0) and not self.is_out_of_arena(x+i,y+j)]

    def get_along_wall_pos(self):
        "return a list of positions along the wall"
        return [(x,y) for x in range(self.size_x) for y in range(self.size_y) if x==0 or x==self.size_x-1 or y==0 or y==self.size_y-1]

    def load_map_from_file(self,file_name):
        self._map_ref=self.load_map(file_name)
        indexes = self.get_start_zone_indexes()
        self.set_cell_list(indexes,value=MapSetting.CLEAR)
        self._update_size()
        self.notify()

    def save_map_to_file(self,filename):
        self.save_map(filename,td_array=self._map_ref)

    def _update_size(self):
        self.size_x = len(self._map_ref[0])
        self.size_y = len(self._map_ref)

    def is_out_of_arena(self,x,y):
        return (x<0 or y<0 or x>=self.size_x or y>=self.size_y)

    def set_map_range(self,x_range,y_range,type):
        "set map_ref cells bounded by x range and y range (both sides inclusive) to `type`"
        for j in range(min(y_range[0],y_range[1]),max(y_range[0],y_range[1])+1):
            if (j<0 or j>=self.size_y): continue
            for i in range(min(x_range[0],x_range[1]),max(x_range[0],x_range[1])+1):
                if (i<0 or i>=self.size_x): continue
                self.set_cell(x=i,y=j,value=type)
        self.notify()

    def get_size_x(self):
        return self.size_x

    def get_size_y(self):
        return self.size_y

    def get_end_zone_center_pos(self):
        "this is hardcoded"
        return self._end_zone_centre_pos if self._end_zone_centre_pos else (self.size_x-2,1)

    def get_start_zone_center_pos(self):
        return self._start_zone_centre_pos if self._start_zone_centre_pos else (1,self.size_y-2)

    def get_end_zone_indexes(self):
        #TODO: so far hardcoded for 3*3 zone area
        x,y=self.get_end_zone_center_pos()
        return [(x+i,y+j) for i in range(-1,2) for j in range(-1,2)]

    def get_start_zone_indexes(self):
        #TODO: so far hardcoded for 3*3 zone area
        x,y=self.get_start_zone_center_pos()
        return [(x+i,y+j) for i in range(-1,2) for j in range(-1,2)]

class MapUI(BaseObserver):
    """
    Observer of MapRef
    """
    CELL_COLORS = {MapRef.OBSTACLE:"blue",MapRef.CLEAR:"green",MapRef.START_ZONE:"yellow",MapRef.END_ZONE:"yellow",MapRef.UNKNOWN:"grey"}
    CELL_SIZE = 2

    _frame = None # frame to draw the map in
    _cells = [] # 2D list of buttons to show cell
    _map_ref = None
    _start_zone_indexes= []
    _end_zone_indexes = []

    def __init__(self,frame,map_ref):
        "create the cells"
        self._map_ref = map_ref
        self._map_ref.add_change_listener(self)
        self._frame = frame
        size_x,size_y=self._map_ref.get_size_x(),self._map_ref.get_size_y()
        self._start_zone_indexes = self._map_ref.get_start_zone_indexes()
        self._end_zone_indexes = self._map_ref.get_end_zone_indexes()
        for i in range(size_y):
                self._cells.append([])
                for j in range(size_x):
                    cell = Button(master=frame,height=self.CELL_SIZE/2,width=self.CELL_SIZE)
                    cell.grid(row=i,column=j)
                    self._cells[i].append(cell)

    def get_cells(self):
        return self._cells

    def paint(self,map_ref=None):
        "paint color for the map cells"
        size_x,size_y=self._map_ref.get_size_x(),self._map_ref.get_size_y()
        for i in range(size_y):
            for j in range(size_x):
                if ((j,i) in self._start_zone_indexes):
                    cell_color = self.CELL_COLORS[MapSetting.START_ZONE]
                elif ((j,i) in self._end_zone_indexes):
                    cell_color = self.CELL_COLORS[MapSetting.END_ZONE]
                else:
                    cell_color = self.CELL_COLORS[self._map_ref.get_cell(j,i)]
                self._cells[i][j].config(bg=cell_color)

    # observer method
    def update(self):
        self.paint()

