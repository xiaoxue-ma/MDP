from abc import ABCMeta, abstractmethod
import time
from threading import Lock
from common.network import SocketServer
from common.pmessage import PMessage
from common.utils import synchronized

class Interface(object):
    """
    abstract synchronized interface
    """
    __metaclass__ = ABCMeta
    _read_lock = None
    _write_lock = None # prevent simultaneous write
    _ready = False

    def __init__(self):
        self._read_lock = Lock()
        self._write_lock = Lock()

    @abstractmethod
    def connect(self): pass

    @abstractmethod
    def disconnect(self): pass

    @abstractmethod
    def _read(self):pass

    @abstractmethod
    def _write(self,msg):pass

    @abstractmethod
    def is_ready(self):
        pass

    def read(self):
        "return a PMessage object"
        self._read_lock.acquire()
        try:
            return self._read()
        finally:
            self._read_lock.release()

    def write(self,msg):
        "msg is PMessage object"
        self._write_lock.acquire()
        try:
            return self._write(msg)
        finally:
            self._write_lock.release()


class SocketServerInterface(Interface):
    """
    interfacing to client as a tcp server
    """

    _server = None  # to be initialized on init
    _name = "Base Interface"
    _server_ip = "localhost"  # addr to bind to
    _server_port = 0
    _write_delay = 0.2 # delay for writing in seconds

    def __unicode__(self):
        return self._name

    def __init__(self):
        super(SocketServerInterface,self).__init__()
        self._server = SocketServer(addr=self._server_ip, port=self._server_port)

    def connect(self):
        self._server.start()
        self._ready = True
        print("Connected to {} at {}".format(self._name, self._server.get_client_addr()))

    def disconnect(self):
        try:
            self._server.close()
            self._ready = False
        except Exception, e:
            print "{} disconnection exception: {}".format(self._name, e)

    def is_ready(self):
        return self._ready

    def _read(self):
        """return a label,Message tuple"""
        try:
            data = self._server.read()
            if (data):
                print("Received data from {} : {}".format(self._name, data))
                return (self._name, PMessage(json_str=data))
        except Exception as e:
            pass


    def _write(self, msg):
        """msg is a Message object"""
        try:
            data = msg.render_msg()
            print("Writing data to {} : {}".format(self._name, data))
            self._server.write(data)
            if (self._write_delay):
                time.sleep(self._write_delay)
        except Exception as e:
            pass