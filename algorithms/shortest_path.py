from common import *
from common.pq import MinQueue
from common.amap import MapRef

class AStarShortestPathAlgo():

    # algo settings
    NON_ACCESS_H_VALUE = 1E6
    UNIT_TURN_COST = 1 # cost for every turn
    END_ALGO_UPON_REACHING_DEST = True

    # algo data
    _nodes = [] # 2D list of nodes
    _map_ref = None # MapRef object
    _target_pos = None # tuple

    def __init__(self,map_ref,target_pos):
        self._map_ref = map_ref
        self._target_pos = target_pos
        self._init_matrices(m=self._map_ref.get_size_x(),n=self._map_ref.get_size_y(),map_ref=self._map_ref)

    def get_shortest_path(self,robot_pos,robot_ori):
        "return a list of commands for walking through the shortest path"
        num_iterations=1
        node_q = MinQueue(key=lambda x:x.get_f()) # queue of (x,y) positions
        start_node = self._nodes[robot_pos[1]][robot_pos[0]]
        start_node.ori = robot_ori
        dest_node = self._nodes[self._target_pos[1]][self._target_pos[0]]
        node_q.enqueue(start_node)
        while(not node_q.is_empty()):
            num_iterations +=1
            # extract min and expand
            cur_node = node_q.dequeue_min()
            cur_node.visited = True
            # may terminate if the current node is the destination
            if (self.END_ALGO_UPON_REACHING_DEST and (cur_node.x,cur_node.y)==self._target_pos):
                break
            neighbours = self.get_neighbour_nodes(cur_node)
            for n in neighbours:
                new_g = self.compute_g_value(cur_node=cur_node,target_node=n)
                new_f = new_g + n.get_h()
                if (n.visited):
                    if (new_f<n.get_f()):
                        n.set_g(new_g)
                        n.parent = cur_node
                        n.ori = AbsoluteOrientation.get_ori_at_dest(start_pos=(cur_node.x,cur_node.y),dest_pos=(n.x,n.y))
                else: # not visited
                    n.parent = cur_node
                    n.set_g(new_g)
                    n.ori = AbsoluteOrientation.get_ori_at_dest(start_pos=(cur_node.x,cur_node.y),dest_pos=(n.x,n.y))
                    node_q.enqueue(n)
        self.print_route(dest_node=dest_node,
                         start_node=start_node)
        print("number of iterations for finding shortest path: {}".format(num_iterations))
        # return list of commands
        return self.get_command_list(start_node=start_node,end_node=dest_node)

    def _get_inaccessible_pos_list(self,map_ref):
        "pos where robot will collide with obstacles"
        pos_list = []
        # 1 all obstacle positions and surrounding positions
        for y in range(map_ref.get_size_y()):
            for x in range(map_ref.get_size_x()):
                if (map_ref.get_cell(x,y)==MapRef.OBSTACLE):
                    pos_list.extend(map_ref.get_surrounding_pos(x,y))
                    pos_list.append((x,y))
        # 2 near wall positions
        pos_list.extend(map_ref.get_along_wall_pos())
        return list(set(pos_list))

    def get_command_list(self,start_node,end_node):
        "return list of commands"
        if (start_node.equals(end_node)):
            return []
        cmd_list = self.get_command_list(start_node=start_node,end_node=end_node.parent)
        cmd_list.extend(self.get_point_move_command(from_node=end_node.parent,to_node=end_node))
        return cmd_list

    def get_point_move_command(self,from_node,to_node):
        "return the list of commands, from_node and to_node should be neighbours"
        action = AbsoluteOrientation.get_turn_action(start_ori=from_node.ori,end_ori=to_node.ori)
        if (action): return [action,PMessage.M_MOVE_FORWARD]
        else: return [PMessage.M_MOVE_FORWARD]

    def print_route(self,dest_node,start_node):
        # terminating case
        if (dest_node.equals(start_node)):
            print("{},{}".format(start_node.x,start_node.y))
            return
        # recursive call
        self.print_route(dest_node=dest_node.parent,start_node=start_node)
        print("{},{}".format(dest_node.x,dest_node.y))

    def compute_g_value(self,cur_node,target_node):
        "return the cost value from cur_pos to target_pos"
        cur_g = cur_node.get_g()
        target_ori = AbsoluteOrientation.get_ori_at_dest(start_pos=(cur_node.x,cur_node.y),dest_pos=(target_node.x,target_node.y))
        additional_g = cur_node.ori.get_minimum_turns_to(target_ori)*self.UNIT_TURN_COST
        return additional_g + cur_g + 1 # 1 is move cost

    def get_neighbour_nodes(self,node):
        "return a list of nodes"
        neighbour_rel_pos = [(-1,0),(1,0),(0,1),(0,-1)]
        neighbour_nodes= []
        for pos in neighbour_rel_pos:
            x,y = (pos[0] + node.x) , (pos[1] + node.y)
            if (not self._map_ref.is_out_of_arena(x,y) and self._nodes[y][x]!=None):
                neighbour_nodes.append(self._nodes[y][x])
        return neighbour_nodes

    def _init_matrices(self,m,n,map_ref):
        "initialize all matrices to m*n, for inaccessible positions, None will be put"
        inaccessible_list = self._get_inaccessible_pos_list(map_ref)
        self._nodes = [[None if (x,y) in inaccessible_list else Node(x,y,self._get_heuristic_value(x,y))
                        for x in range(m)]
                       for y in range(n)]

    def _get_heuristic_value(self,x,y):
        return abs(x-self._target_pos[0]) + abs(y-self._target_pos[1]) if self._map_ref.get_cell(x,y)==MapRef.CLEAR else self.NON_ACCESS_H_VALUE

class Node():

    INIT_H_VALUE = 0

    parent = None # pointer to another node
    _h = INIT_H_VALUE
    _g = 0
    _f = _h
    visited = False
    ori = None
    x=0 # coordinate
    y=0

    def __init__(self,x,y,h):
        self.x = x
        self.y = y
        self.set_h(h)

    def set_h(self,h):
        self._h = h
        self.recompute_f()

    def set_g(self,g):
        self._g = g
        self.recompute_f()

    def recompute_f(self):
        self._f = self._h + self._g

    def get_h(self):
        return self._h

    def get_g(self):
        return self._g

    def get_f(self):
        return self._f

    def equals(self,a_node):
        "check whether a_node has the same coordinate of self"
        return self.x==a_node.x and self.y==a_node.y