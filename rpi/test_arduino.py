__author__ = 'Boss'
import thread
import time
from arduino_interface import ArduinoInterface


class ArduinoTest:
    def __init__(self):
        self.arduino = ArduinoInterface()

    def connect_arduino(self):
        connected = self.arduino.connect()
        while not connected:
            time.sleep(1)
            connected = self.arduino.connect()

    def write_arduino(self):
        self.arduino.flush()
        while True:
            x = (raw_input())
            self.arduino.write(x + "\n")

    def read_arduino(self):
        while True:
            val = self.arduino.read()
            if val is not None:
                time.sleep(0)

    def start_thread(self):
        try:
            thread.start_new_thread(self.write_arduino, ())
            thread.start_new_thread(self.read_arduino, ())
        except Exception, e:
            print "Unable to start thread!"
            print "Error: %s" % str(e)

if __name__ == "__main__":
    print(raw_input())
    test = ArduinoTest()
    test.connect_arduino()
    test.start_thread()
