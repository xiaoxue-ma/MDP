import time
from bluetooth import *
from config import *
from message import *


class AndroidInterface(object):
    _write_delay = 0.05

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
            print("BT--Connected to %s on channel %s" % (str(client_info), str(port)))
            self.status = True
            return True

        except Exception, e:
            print "BT--connection exception: %s" % str(e)
            self.status = False
            self.reconnect()
            return False

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
            time.sleep(2)
            self.connect()

    def read(self):
        try:
            msg = self.client_sock.recv(2048)
            print "BT--Read from Android: %s" % str(msg)
            msg = json.loads(msg)
            msg = msg.get("msg")
            print "BT--After conversion %s" % str(msg)
            return android_to_algo(msg)
        except Exception, e:
            print "BT--read exception: %s" % str(e)
            self.reconnect()

    def write(self, msg):
        try:
            print "BT--Write to Android: %s" % str(msg)
            msg = algo_to_android(msg)
            print "BT--After conversion: %s" % str(msg)
            self.client_sock.send(msg)
        except Exception, e:
            print "BT--write exception: %s" % str(e)
            self.reconnect()