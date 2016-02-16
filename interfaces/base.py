from abc import ABCMeta,abstractmethod
import socket

from common.pmessage import PMessage

class Interface():
    """
    abstract class for defining interface
    interfacing to server
    """

    _sock = None
    _name = "Base Interface"

    def connect(self):
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self._sock = sock
        server_ip = self._get_server_ip()
        server_port = self._get_server_port()
        server_address = (server_ip,server_port)
        sock.connect(server_address)
        print("Connected to {} at {}:{}".format(self._name,server_ip,server_port))

    def _get_server_ip(self):
        return "localhost"

    def _get_server_port(self):
        raise NotImplementedError()

    def disconnect(self):
        try:
            self._sock.close()
        except Exception, e:
            print "{} disconnection exception: {}".format(self._name,e)

    def read(self):
        "return a label,Message tuple"
        data = self._sock.recv(1024)
        if (data):
            print("Received data from {} : {}".format(self._name,data))
            try:
                msg_obj = PMessage(json_str=data)
                return (self._name,PMessage(json_str=data))
            except:
                pass

    def write(self,msg):
        "msg is a Message object"
        data=msg.render_msg()
        print("Writing data to {} : {}".format(self._name,data))
        self._sock.sendall(data)
