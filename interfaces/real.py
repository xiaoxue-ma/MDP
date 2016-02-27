"""
set of real device communication interfaces
"""
import serial, time
from bluetooth import *

WIFI_IP = "192.168.2.2"
WIFI_PORT = 3053
BAUD = 115200
SER_PORT0 = "/dev/ttyACM0"
SER_PORT1 = "/dev/ttyACM1"
N7_MAC = "08:60:6E:A5:A4:1E"
UUID = "2016Grp1"
BT_PORT = 4


class PCInterface(object):
    pass


class ArduinoInterface(object):
    def __init__(self):
        self.baudrate = BAUD
        self.ser = 0

    def connect(self):
        # connect to serial port
        try:
            print "Trying to connect to Arduino..."
            self.ser = serial.Serial(SER_PORT0, self.baudrate, timeout=3)
            time.sleep(1)

            if (self.ser != 0):
                print "Connected to Arduino!"
                self.read()
                return 1

        except Exception, e:
            self.ser = serial.Serial(SER_PORT1, self.baudrate, timeout=3)
            return 1

    def write(self, msg):
        try:
            self.ser.write(msg + "|")  # write msg with | as end of msg
        except Exception, e:
            print "Arduino write exception: %s" % str(e)

    def read(self):
        try:
            msg = self.ser.readline()  # read msg from arduino sensors
            return msg
        except Exception, e:
            print "Arduino read exception: %s" % str(e)


class AndroidInterface(object):
    def __init__(self):
        self._status = False

    def connect(self):
        try:
            self.server_sock = BluetoothSocket(RFCOMM)
            self.server_sock.bind(("", BT_PORT))
            self.server_sock.listen(2)
            port = self.server_sock.getsockname()[1]
            advertise_service(self.server_sock, "SampleServer",
                              service_id=UUID,
                              service_classes=[UUID, SERIAL_PORT_CLASS],
                              profiles=[SERIAL_PORT_PROFILE],
                              # protocols = [ OBEX_UUID ]
            )
            self.client_sock, client_info = self.server_sock.accept()

            if client_info[0] != N7_MAC:
                print "BT--Unauthorized device, disconnecting..."
                self._status = False
                return

            print("BT--Accepted connection from %s on channel %d" % str(client_info) % port)
            self._status = True

        except Exception, e:
            print "BT--connection exception: %s" % str(e)
            self._status = False

    def disconnect(self):
        try:
            self.client_sock.close()
            self.server_sock.close()
            print("BT--Disconnected to Android")
        except Exception, e:
            print "BT--disconnection exception: %s" % str(e)

    def reconnect(self):
        connected = self._status
        while not connected:
            print "BT--reconnecting..."
            self.disconnect()
            self.connect()

    def write(self, msg):
        try:
            self.client_sock.send(msg)
            print "BT--Write to Android: %s" % msg
        except Exception, e:
            print "BT--write exception: %s" % str(e)
            self.reconnect()

    def read(self):
        try:
            msg = self.client_sock.recv(1024)
            print "BT--Read from Android: %s" % msg
            return msg
        except Exception, e:
            print "BT--read exception: %s" % str(e)
            self.reconnect()