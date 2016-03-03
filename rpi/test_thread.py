import time
import thread
from pc_interface import PCInterface


class ThreadTest():
    def __init__(self):
        self.pc = PCInterface()

    def connect_pc(self):
        connected = self.pc.connect()
        while not connected:
            time.sleep(1)
            connected = self.pc.connect()

    def write_pc(self):
        # self.pc.flush()
        # while True:
            x = (raw_input())
            self.pc.write(x + "\n")

    def read_pc(self):
        while True:
            val = self.pc.read()
            if val is not None and len(val) > 0:
                time.sleep(0)

    def start_thread(self):
        try:
            thread.start_new_thread(self.write_pc, ())
            thread.start_new_thread(self.read_pc, ())
        except Exception, e:
            print "Unable to start thread!"
            print "Error: %s" % str(e)

if __name__ == "__main__":
    test = ThreadTest()
    test.connect_pc()
    test.start_thread()
    while True:
        pass
