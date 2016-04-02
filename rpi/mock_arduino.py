import time
from cache import Rpi_Queue
from message import *
import socket

SER_BAUD = 115200
SER_PORT = "/dev/ttyACM"


class ArduinoInterface(object):
    _write_delay = 0.5
    _calib_delay = 1

    def __init__(self):
        self.status = False
        self.ser = None
        self.port_no = 1
        self.writeq = Rpi_Queue()

    def connect(self):
        print("SER--connected")
        return True

    def disconnect(self):
        pass

    def reconnect(self):
        pass

    def read(self):
        try:
            msg = raw_input('SERREADING')
            if msg != "":
                print("SER--Read from Arduino: %s" % str(msg))
                if len(msg) > 5:
                    if msg[0] != 'T':
                        return msg
                else:
                    msg = msg[0]
                    if msg <= '8':
                        msg = arduino_to_algo(msg)
                        print("SER--After conversion: %s" % str(msg))
                        return msg
        except Exception, e:
            print("SER--read exception: %s" % str(e))
            self.reconnect()

    def write(self, msg):
        try:
            print("SER--Write to Arduino: %s" % str(msg))
            realmsg = algo_to_arduino(msg)
            print("SER--After conversion: %s" % str(realmsg))
            if realmsg:
                if realmsg == 'i' or realmsg == 'o':
                    time.sleep(self._calib_delay - self._write_delay)
                time.sleep(self._write_delay)
        except Exception, e:
            print("SER--write exception: %s" % str(e))
            self.writeq.enqueue(msg)

    def write_from_q(self, msg):
        try:
            print("SER--Write to Arduino from Cache: %s" % str(msg))
            realmsg =algo_to_arduino(msg)
            print("SER--After conversion from Cache: %s" % str(msg))
            if realmsg:
                if realmsg == 'i' or realmsg == 'o':
                    time.sleep(self._calib_delay - self._write_delay)
                time.sleep(self._write_delay)
            return True
        except Exception, e:
            print("SER--write exception from Cache: %s" % str(e))
            self.reconnect()
            return False
