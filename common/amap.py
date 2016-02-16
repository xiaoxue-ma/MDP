from Tkinter import *

from common import *
from common.popattern import *

class MapRef(BasePublisher):
    """
    internal representation of the arena map
    """
    DEFAULT_MAP_SIZE_X = 20
    DEFAULT_MAP_SIZE_Y = 15

    # possible values of the each cell
    CLEAR = 0
    OBSTACLE = 1
    UNKNOWN = 2
    START_ZONE = 3
    END_ZONE = 4

    DEFAULT_CELL_VALUE = UNKNOWN
    VALID_CELL_VALUES = [CLEAR,OBSTACLE,UNKNOWN,START_ZONE,END_ZONE]
    START_ZONE_INDICES = [(x,y) for x in range(3) for y in range(3)]

    _map_ref = [] # 2D matrix
    size_x = 0
    size_y = 0

    _listeners = [] # list of observers

    def __init__(self,x=None,y=None,default=None):
        if (x and y and default):
            self._map_ref = [[default for _ in range(x)] for __ in range(y)]
        else:
            self._map_ref = [[self.DEFAULT_CELL_VALUE for _ in range(self.DEFAULT_MAP_SIZE_X)] for __ in range(self.DEFAULT_MAP_SIZE_Y)]
        self._update_size()

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

    def load_map_from_file(self,file_name):
        f = open(file_name,mode="r")
        lines = f.readlines()
        map_2d = [] # list of list
        for line in lines:
            map_2d.append([int(i) for i in line if i.isdigit() and int(i) in self.VALID_CELL_VALUES])
        self._map_ref = map_2d
        self._update_size()
        self.notify()

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
        return self.size_x-2,self.size_y-2

    def get_start_zone_center_pos(self):
        return 1,1

class MapUI(BaseObserver):
    """
    Observer of MapRef
    """
    CELL_COLORS = {MapRef.OBSTACLE:"blue",MapRef.CLEAR:"green",MapRef.START_ZONE:"yellow",MapRef.END_ZONE:"yellow",MapRef.UNKNOWN:"grey"}
    CELL_SIZE = 2

    _frame = None # frame to draw the map in
    _cells = [] # 2D list of buttons to show cell
    _map_ref = None

    def __init__(self,frame,map_ref):
        "create the cells"
        self._map_ref = map_ref
        self._map_ref.add_change_listener(self)
        self._frame = frame
        size_x,size_y=self._map_ref.get_size_x(),self._map_ref.get_size_y()
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
                cell_color = self.CELL_COLORS[self._map_ref.get_cell(j,i)]
                self._cells[i][j].config(bg=cell_color)

    # observer method
    def update(self):
        self.paint()