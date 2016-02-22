from abc import ABCMeta,abstractmethod
import socket
from common.network import SocketServer
from common.pmessage import PMessage

class Interface():
    """
    abstract class for defining interface
    interfacing to client
    """

    _server = None # to be initialized on init
    _name = "Base Interface"
    _server_ip = "localhost" # addr to bind to
    _server_port = 0

    def __init__(self):
        self._server = SocketServer(addr=self._server_ip,port=self._server_port)

    def connect(self):
        self._server.start()
        print("Connected to {} at {}".format(self._name,self._server.get_client_addr()))

    def disconnect(self):
        try:
            self._server.close()
        except Exception, e:
            print "{} disconnection exception: {}".format(self._name,e)

    def read(self):
        "return a label,Message tuple"
        data = self._server.read()
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
        self._server.write(data)
