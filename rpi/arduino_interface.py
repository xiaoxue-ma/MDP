import serial
from config import *
import time

class ArduinoInterface(object):
    def __init__(self):
        self.status = False
        self.name = "arduino"

    def connect(self):
        try:
            self.ser = serial.Serial(SER_PORT, 9600)
            time.sleep(2)
            if self.ser is not None:
                self.status = True
                print "SER--Connected to Arduino!"
            return self.status
        except Exception, e:
            print "SER--connection exception: %s" % str(e)
            self.status = False
            # self.reconnect()

    def disconnect(self):
        if self.ser.is_open:
            self.ser.close()
            self.status = False
            print "SER--Disconnected to Arduino!"

    def reconnect(self):
        if not self.status:
            print "SER--reconnecting..."
            self.disconnect()
            self.connect()

    def read(self):
        try:
            msg = self.ser.readline()
            if msg != "":
                print "SER--Read from Arduino: %s" % str(msg)
                return msg
        except Exception, e:
            print "SER--read exception: %s" % str(e)
            # self.reconnect()

    def write(self, msg):
        try:
            self.ser.write(msg)
            print "SER--Write to Arduino: %s" % str(msg)
        except Exception, e:
            print "SER--write exception: %s" % str(e)
            # self.reconnect()

    def flush(self):
        self.ser.flushInput()
        self.ser.flushOutput()