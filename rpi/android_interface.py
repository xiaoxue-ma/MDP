__author__ = 'Boss'
from bluetooth import *
from config import *

class AndroidInterface(object):
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