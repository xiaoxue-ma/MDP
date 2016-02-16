"""
Min queue to be used in A* algo
"""

class MinQueue():

    _list = []
    _key_func = None # function used to sort the list

    def __init__(self,key):
        self._key_func = key

    def enqueue(self,item):
        self._list.append(item)

    def dequeue_min(self):
        self._list.sort(key=self._key_func)
        min = self._list[0]
        del self._list[0]
        return min

    def is_empty(self):
        return len(self._list)==0