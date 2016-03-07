"""
set of real device communication interfaces
"""
import socket
import serial
from bluetooth import *

import time
from base import Interface
from common import PMessage
from common.constants import ARDUINO_LABEL,ANDROID_LABEL

WIFI_HOST = "192.168.1.1"
WIFI_PORT = 50001
SER_BAUD = 115200
SER_PORT = "/dev/ttyACM0"
N7_MAC = "08:60:6E:A5:A5:86"
BT_UUID = "00001101-0000-1000-8000-00805F9B34FB"
BT_PORT = 4

TO_SER = dict({PMessage.M_MOVE_FORWARD: "0", PMessage.M_TURN_RIGHT: "1", PMessage.M_TURN_LEFT: "2",
               PMessage.M_TURN_BACK: "3", PMessage.M_START_EXPLORE: "4", PMessage.M_END_EXPLORE: "5",
               PMessage.M_START_FASTRUN: "6", })
FROM_SER = dict({"0": PMessage.M_MOVE_FORWARD, "1": PMessage.M_TURN_RIGHT, "2": PMessage.M_TURN_LEFT,
                 "3": PMessage.M_TURN_BACK, "4": PMessage.M_START_EXPLORE, "5": PMessage.M_END_EXPLORE,
                 "6": PMessage.M_START_FASTRUN, })

class ArduinoInterface(Interface):
    name = ARDUINO_LABEL

    def __init__(self):
        super(ArduinoInterface,self).__init__()
        self.status = False

    def connect(self):
        try:
            self.ser = serial.Serial(SER_PORT, SER_BAUD, timeout=3)
            time.sleep(2)
            if self.ser is not None:
                self.status = True
                print "SER--Connected to Arduino!"
        except Exception, e:
            print "SER--connection exception: %s" % str(e)
            self.status = False
            # self.reconnect()

    def is_ready(self):
        return self.status

    def disconnect(self):
        if self.ser.is_open:
            self.ser.close()
            self.status = False
            print "SER--Disconnected to Arduino!"


    def _read(self):
        try:
            msg = self.ser.readline()
            if msg != "":
                print "SER--Read from Arduino: %s" % str(msg)
                if len(msg) > 1:
                    if msg[0] != 'T':
                        realmsg = PMessage(type=PMessage.T_MAP_UPDATE, msg=msg)
                        return (self.name,realmsg)
                else:
                    msg = msg[0]
                    if msg < '4':
                        realmsg = PMessage(type=PMessage.T_ROBOT_MOVE, msg=FROM_SER.get(msg[0]))
                        return (self.name,realmsg)

        except Exception, e:
            print "SER--read exception: %s" % str(e)
            # self.reconnect()

    def _write(self, msg):
        try:
            realmsg = TO_SER.get(msg.get_msg())
            if realmsg:
                self.ser.write(realmsg)
                print "SER--Write to Arduino: %s" % str(msg)
        except Exception, e:
            print "SER--write exception: %s" % str(e)
            # self.reconnect()


class AndroidInterface(Interface):

    name = ANDROID_LABEL
    _write_delay = 1

    def __init__(self):
        super(AndroidInterface,self).__init__()
        self.status = False

    def connect(self):
        try:
            self.server_sock = BluetoothSocket(RFCOMM)
            self.server_sock.bind(("", BT_PORT))
            self.server_sock.listen(2)
            port = self.server_sock.getsockname()[1]
            advertise_service(self.server_sock, "SampleServer",
                              service_id=BT_UUID,
                              service_classes=[BT_UUID, SERIAL_PORT_CLASS],
                              profiles=[SERIAL_PORT_PROFILE],
            )
            self.client_sock, client_info = self.server_sock.accept()

            # if client_info[0] != N7_MAC:
            # print "BT--Unauthorized device, disconnecting..."
            #     return

            print("BT--Connected to %s on channel %s" % (str(client_info), str(port)))
            self.status = True

        except Exception, e:
            print "BT--connection exception: %s" % str(e)
            self.status = False
            # self.reconnect()

    def is_ready(self):
        return self.status

    def disconnect(self):
        try:
            self.client_sock.close()
            self.server_sock.close()
            self.status = False
            print("BT--Disconnected to Android!")
        except Exception, e:
            print "BT--disconnection exception: %s" % str(e)


    def _read(self):
        try:
            msg = self.client_sock.recv(2048)
            print "BT--Read from Android: %s" % str(msg)
            return (self.name, PMessage(json_str=msg))
        except Exception, e:
            print "BT--read exception: %s" % str(e)
            # self.reconnect()


    def _write(self, msg):
        try:
            if msg.get_msg() == "exploreend":
                msg._msg = "ee"
            msg = msg.render_msg()
            self.client_sock.send(msg)
            time.sleep(self._write_delay)
            print "BT--Write to Android: %s" % str(msg)
        except Exception, e:
            print "BT--write exception: %s" % str(e)
