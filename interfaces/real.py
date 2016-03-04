"""
set of real device communication interfaces
"""
import socket
import serial
from bluetooth import *
import time
from base import Interface
from common import PMessage

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


class PCInterface(Interface):
    def __init__(self):
        self.status = False
        self.name = "pc"

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind((WIFI_HOST, WIFI_PORT))
            self.socket.listen(1)
            self.client_sock, self.client_addr = self.socket.accept()
            print "WIFI--Connected to ", self.client_addr
            self.status = True
            # receive the first message from client, know the client address
            # data, self.pcaddr = self.ipsock.recv(1024)
        except Exception, e:
            print "WIFI--connection exception: %s" % str(e)
            self.status = False
            self.reconnect()

    def disconnect(self):
        try:
            self.socket.close()
            self.status = False
        except Exception, e:
            print "WIFI--disconnection exception: %s" % str(e)

    def reconnect(self):
        if not self.status:
            print "WIFI--reconnecting..."
            self.disconnect()
            self.connect()

    def read(self):
        try:
            msg = self.client_sock.recv(1024)
            print "WIFI--Read from PC: %s" % str(msg)
            return (self.name, PMessage(json_str=msg))
        except Exception, e:
            print "WIFI--read exception: %s" % str(e)
            self.reconnect()

    def write(self, msg):
        try:
            msg = msg.render_msg()
            self.client_sock.sendto(msg, self.client_addr)
            print "WIFI--Write to PC: %s" % str(msg)
        except Exception, e:
            print "WIFI--write exception: %s" % str(e)
            self.reconnect()


class ArduinoInterface(Interface):
    def __init__(self):
        self.status = False
        self.name = "arduino"

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
                if len(msg) > 1:
                    realmsg = PMessage(type=PMessage.T_MAP_UPDATE, msg=msg)
                else:
                    realmsg = PMessage(type=PMessage.T_ROBOT_MOVE, msg=FROM_SER.get(msg[0]))
                return realmsg
        except Exception, e:
            print "SER--read exception: %s" % str(e)
            # self.reconnect()

    def write(self, msg):
        try:
            msg = msg.render_msg()
            realmsg = TO_SER.get(msg.get_msg())
            if realmsg:
                self.ser.write(realmsg)
                print "SER--Write to Arduino: %s" % str(msg)
        except Exception, e:
            print "SER--write exception: %s" % str(e)
            # self.reconnect()


class AndroidInterface(Interface):
    def __init__(self):
        self.status = False
        self.name = "android"

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
            self.reconnect()

    def disconnect(self):
        try:
            self.client_sock.close()
            self.server_sock.close()
            self.status = False
            print("BT--Disconnected to Android!")
        except Exception, e:
            print "BT--disconnection exception: %s" % str(e)

    def reconnect(self):
        if not self.status:
            print "BT--reconnecting..."
            self.disconnect()
            self.connect()

    def read(self):
        try:
            msg = self.client_sock.recv(1024)
            print "BT--Read from Android: %s" % str(msg)
            return (self.name, PMessage(json_str=msg))
        except Exception, e:
            print "BT--read exception: %s" % str(e)
            self.reconnect()

    def write(self, msg):
        try:
            msg = msg.render_msg()
            self.client_sock.send(msg)
            print "BT--Write to Android: %s" % str(msg)
        except Exception, e:
            print "BT--write exception: %s" % str(e)
            self.reconnect()
