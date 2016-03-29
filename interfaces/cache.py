import Queue

class Cache_Rpi():
    def __init__(self):
	self.q = Queue.Queue()

    def enqueue(self, msg):
        self.q.put(msg)

    def dequeue(self):
        if not self.q.empty():
	    return self.q.get()

    def is_empty(self):
		return self.q.empty() 
