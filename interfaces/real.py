"""
set of real device communication interfaces
"""
import socket
import serial
from bluetooth import *
from interfaces.base import Interface

WIFI_HOST = "192.168.1.1"
WIFI_PORT = 50001
SER_BAUD = 115200
SER_PORT = "/dev/ttyACM0"
N7_MAC = "50:46:5D:84:91:20"
BT_UUID = "00001101-0000-1000-8000-00805F9B34FB"
BT_PORT = 4


class PCInterface(Interface):
    def __init__(self):
        self.status = False

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind((WIFI_HOST, WIFI_PORT))
            self.socket.listen(1)
            self.client_sock, self.client_addr = self.socket.accept()
            print "WIFI--Connected to ", self.client_addr
            self.status = True
            # receive the first message from client, know the client address
            #data, self.pcaddr = self.ipsock.recv(1024)
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
            return msg
        except Exception, e:
            print "WIFI--read exception: %s" % str(e)
            self.reconnect()

    def write(self, msg):
        try:
            self.client_sock.sendto(msg, self.client_addr)
            print "WIFI--Write to PC: %s" % str(msg)
        except Exception, e:
            print "WIFI--write exception: %s" % str(e)
            self.reconnect()


class ArduinoInterface(Interface):
    def __init__(self):
        self.status = False

    def connect(self):
        try:
            self.ser = serial.Serial(SER_PORT, SER_BAUD, timeout=3)
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
                return msg
        except Exception, e:
            print "SER--read exception: %s" % str(e)
            self.reconnect()

    def write(self, msg):
        try:
            self.ser.write(msg + "|")
            print "SER--Write to Arduino: %s" % str(msg)
        except Exception, e:
            print "SER--write exception: %s" % str(e)
            self.reconnect()


class AndroidInterface(Interface):
    def __init__(self):
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

            if client_info[0] != N7_MAC:
                print "BT--Unauthorized device, disconnecting..."
                return

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
            return msg
        except Exception, e:
            print "BT--read exception: %s" % str(e)
            self.reconnect()

    def write(self, msg):
        try:
            self.client_sock.send(msg)
            print "BT--Write to Android: %s" % str(msg)
        except Exception, e:
            print "BT--write exception: %s" % str(e)
            self.reconnect()
