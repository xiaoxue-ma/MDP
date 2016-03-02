import socket
from config import *

class PCInterface(object):
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