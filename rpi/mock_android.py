import time
# from bluetooth import *
from config import *
from message import *


class AndroidInterface(object):
    _write_delay = 0.05
    first = False

    def __init__(self):
        self.status = False

    def connect(self):
        self.first = True
        print("BT--Connected!")
        return True

    def disconnect(self):
        pass

    def reconnect(self):
        pass

    def read(self):
        if self.first:
            msg = raw_input('BTR')
            print "BT--Read from Android: %s" % str(msg)
            msg = json.loads(msg)
            msg = msg.get("msg")
            print "BT--Returned %s" % str(android_to_algo(msg))
            self.first = False
            return android_to_algo(msg)



    def write(self, msg):
        try:
            print "BT--Write to Android: %s" % str(msg)
            msg = algo_to_android(msg)
            print "BT--After conversion: %s" % str(msg)

        except Exception, e:
            print "BT--write exception: %s" % str(e)
            self.reconnect()