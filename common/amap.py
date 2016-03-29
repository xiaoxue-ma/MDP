import os
import math
import re
from Tkinter import *
from abc import ABCMeta,abstractmethod
from bitarray import bitarray

from common import *
from common.debug import debug,DEBUG_COMMON
from common.popattern import *

class MapSetting():
    # map settings
    DEFAULT_MAP_SIZE_X = 15
    DEFAULT_MAP_SIZE_Y = 20
    DEFAULT_START_POS = (1,18)
    DEFAULT_END_POS = (13,1)
    #
    # DEFAULT_MAP_SIZE_X = 10
    # DEFAULT_MAP_SIZE_Y = 15
    # DEFAULT_START_POS = (1,13)
    # DEFAULT_END_POS = (8,1)

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
        debug("Map loaded: {}".format(self.to_hex(arr.tobytes())),DEBUG_COMMON)
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
        debug("Map saved: {}".format(self.to_hex(arr.tobytes())),DEBUG_COMMON)
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
    _map_ref = None # 2D matrix
    _fixed_list = None # list of positions that cannot be reassigned value

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
        self._fixed_list = []
        if (x and y and default):
            self._map_ref = [[default for _ in range(x)] for __ in range(y)]
        else:
            self._map_ref = [[self.DEFAULT_CELL_VALUE for _ in range(self.DEFAULT_MAP_SIZE_X)] for __ in range(self.DEFAULT_MAP_SIZE_Y)]
        # set start zone to be clear
        self._update_size()
        indexes = self.get_start_zone_indexes() + self.get_end_zone_indexes()
        self.set_fixed_cells(indexes,value=MapSetting.CLEAR)
        self.notify()

    def is_fully_explored(self):
        return self.get_unknown_percentage()==0

    def get_unknown_percentage(self):
        map_size = self.size_y * self.size_x
        num_unknown_cells = sum([1 for x in range(self.size_x) for y in range(self.size_y) if self.get_cell(x,y)==self.UNKNOWN])
        return int(math.ceil(100.0*num_unknown_cells/map_size))

    def refresh(self):
        self.notify()

    def get_cell(self,x,y):
        return self._map_ref[y][x]

    def set_cell(self,x,y,value,notify=True):
        if ((x,y) in self._fixed_list):
            return
        self._map_ref[y][x] = value
        if (notify):
            self.notify([(x,y)])

    def set_cell_list(self,pos_list,value,notify=True,maintain_obstacle=True,maintain_clear=False):
        "pos_list should be a list of (x,y), if maintain_obstacle is true, then the cells that are already set to be obstacle will NOT be updated"
        for x,y in pos_list:
            if ((x,y) in self._fixed_list):
                continue
            if (not self.is_out_of_arena(x,y)):
                if (maintain_obstacle and self.get_cell(x,y)==MapSetting.OBSTACLE):
                    continue
                if (maintain_clear and self.get_cell(x,y)==MapSetting.CLEAR):
                    continue
                self.set_cell(x,y,value,notify=False)
        if (notify):
            self.notify(pos_list)

    def set_fixed_cells(self,pos_list,value):
        "set cells' value and mark them as fixed"
        self.set_cell_list(pos_list,value,maintain_obstacle=False,maintain_clear=False)
        self._fixed_list = list(set(self._fixed_list + pos_list))

    def are_all_unaccessible(self,pos_list):
        "return true if all positions in the list are not accessbile"
        for x,y in pos_list:
            if ((not self.is_out_of_arena(x,y)) and self.get_cell(x,y)!=MapSetting.OBSTACLE):
                return False
        return True

    def is_along_wall(self,x,y):
        return x==0 or x==self.size_x-1 or y==0 or y==self.size_y-1

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

    def get_num_obstacles(self):
        return sum([1 if self.get_cell(x,y)==MapSetting.OBSTACLE else 0
                    for x in range(self.size_x) for y in range(self.size_y)])

    def set_unknowns_as_clear(self):
        "set all unknown cells as clear"
        for x in range(self.size_x):
            for y in range(self.size_y):
                if (self.get_cell(x,y)==MapSetting.UNKNOWN):
                    self.set_cell(x,y,MapSetting.CLEAR)

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

    def notify(self,data=None):
        if (data!=None):
            super(MapRef,self).notify(data=data)
        else:
            super(MapRef,self).notify(data=[(x,y)
                                            for x in range(self.size_x) for y in range(self.size_y)])



class MapRefWithBuffer(MapRef):
    _buffered_changes = None

    def reset(self,*args,**kwargs):
        self._buffered_changes = set()
        super(MapRefWithBuffer,self).reset(*args,**kwargs)


    def set_cell(self,x,y,value,notify=True):
        super(MapRefWithBuffer,self).set_cell(x,y,value,notify)
        if (not self.is_out_of_arena(x,y)):
            self._buffered_changes.add((x,y,self.get_cell(x,y)))

    def set_cell_list(self,pos_list,value,notify=True,maintain_obstacle=True,maintain_clear=False):
        super(MapRefWithBuffer,self).set_cell_list(pos_list,value,notify,maintain_obstacle,maintain_clear)
        for x,y in pos_list:
            if (not self.is_out_of_arena(x,y)):
                self._buffered_changes.add((x,y,self.get_cell(x,y)))

    def retrieve_updated_cells(self):
        "return the whole buffer and empty it"
        reply = list(self._buffered_changes)
        self._buffered_changes = set()
        return reply


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
        "paint color for all map cells"
        size_x,size_y=self._map_ref.get_size_x(),self._map_ref.get_size_y()
        self.paint_list([(x,y) for x in range(size_x) for y in range(size_y)])

    def paint_list(self,pos_list):
        "paint color for a list of map cells"
        for pos in pos_list:
            x,y=pos[0],pos[1]
            if (not self._map_ref.is_out_of_arena(x,y)):
                cell_color = self.get_cell_color(x,y)
                self._cells[y][x].config(bg=cell_color)
                self._cells[y][x].config(highlightbackground=cell_color)

    def get_cell_color(self,x,y):
        if ((x,y) in self._start_zone_indexes):
            return self.CELL_COLORS[MapSetting.START_ZONE]
        elif ((x,y) in self._end_zone_indexes):
            return self.CELL_COLORS[MapSetting.END_ZONE]
        else:
            return self.CELL_COLORS[self._map_ref.get_cell(x,y)]

    def paint_text(self,x,y,text):
        self._cells[y][x].config(text=text)

    def paint_color(self,x,y,color):
        self._cells[y][x].config(bg=color)

    # observer method
    def update(self,data=None):
        "the data should be a list of positions"
        if (not data):
            self.paint()
        else:
            self.paint_list(data)

