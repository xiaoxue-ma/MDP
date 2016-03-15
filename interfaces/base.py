from abc import ABCMeta, abstractmethod
import time
import socket
from threading import Lock
from common.pmessage import PMessage,ValidationException
from common.utils import synchronized,SimpleQueue
from common.debug import debug,DEBUG_INTERFACE,DEBUG_VALIDATION

class Interface(object):
    """
    abstract synchronized interface
    """
    __metaclass__ = ABCMeta
    _read_lock = None
    _write_lock = None # prevent simultaneous write
    _ready = False
    _name = "interface"
    _msg_buffer = None # a queue

    def __unicode__(self):
        return self._name

    def __init__(self):
        self._read_lock = Lock()
        self._write_lock = Lock()
        self._msg_buffer = SimpleQueue()

    @abstractmethod
    def connect(self):
        "should set_ready is connection is successful"
        pass

    @abstractmethod
    def disconnect(self):
        "should set_not_ready is disconnect successfully"
        pass

    def reconnect(self):
        self.disconnect()
        self.connect()

    @abstractmethod
    def read(self):
        "return list of pmessage objects"
        pass

    @abstractmethod
    def write(self,msg):
        "msg is pmessage object"
        pass

    def is_ready(self):
        return self._ready

    def set_ready(self):
        self._ready = True

    def set_not_ready(self):
        self._ready = False

class BaseSocketInterface(Interface):
    """
    interfacing using socket
    """

    _connection = None  # connection object
    _name = "Base Socket Interface"
    _server_ip = "localhost"  # addr to bind to
    _server_port = 0
    _write_delay = 0.2 # delay for writing in seconds
    _recv_size= 2048


    def __init__(self,ip=None,port=None):
        super(BaseSocketInterface,self).__init__()
        if (ip): self._server_ip = ip
        if (port): self._server_port = port


    def set_write_delay(self,delay):
        self._write_delay = delay

    def connect(self):
        debug("waiting to connect to {}".format(self._name),DEBUG_INTERFACE)
        self._connection = self._connect(server_ip=self._server_ip,server_port=self._server_port)
        self.set_ready()
        debug("{} connected to {}:{}".format(self._name, self._server_ip,self._server_port),DEBUG_INTERFACE)

    def _connect(self,server_ip,server_port):
        raise NotImplementedError("_connect not implemented")

    def disconnect(self):
        try:
            self._connection.close()
            self.set_not_ready()
        except Exception, e:
            print "{} disconnection exception: {}".format(self._name, e)

    def read(self):
        """return a Message object, None if invalid message is received"""
        if (not self._msg_buffer.is_empty()):
            return self._msg_buffer.dequeue()

        if (not self._connection):
            raise Exception("connection not ready, cannot read")
        data = None
        try:
            data = self._connection.recv(self._recv_size)
        except Exception as e:
            debug("Read exception: {}".format(e),DEBUG_INTERFACE)
            if (hasattr(e,'errno') and getattr(e,'errno')==10054):
                self.reconnect()
            return None

        if (data):
            debug("Received data from {} : {}".format(self._name, data),DEBUG_INTERFACE)
            try:
                pmsgs = PMessage.load_messages_from_json(json_str=data)
                if (pmsgs):
                    for msg in pmsgs:
                        self._msg_buffer.enqueue(msg)
                    return self._msg_buffer.dequeue()
            except ValidationException as e:
                debug("Validation exception: {}".format(e.message),DEBUG_VALIDATION)
                return None


    def write(self, msg):
        """msg is a Message object"""
        if (not self._connection):
            raise Exception("connectio not ready, cannot write")
        data = msg.render_msg()
        debug("{} Writing data: {}".format(self._name, data),DEBUG_INTERFACE)
        try:
            self._connection.sendall(data)
            if (self._write_delay):
                time.sleep(self._write_delay)
        except Exception as e:
            debug("Write exception: {}".format(e),DEBUG_INTERFACE)
            if (hasattr(e,'errno') and getattr(e,'errno')==10054):
                self.reconnect()
            return None

class SocketClientInterface(BaseSocketInterface):
    """
    interfacing to server as tcp client
    """
    _name = "TCP Client Interface"

    def __init__(self,ip=None,port=None):
        super(SocketClientInterface,self).__init__(ip,port)

    def _connect(self,server_ip,server_port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (server_ip, server_port)
        connected = False
        while(not connected):
            try:
                sock.connect(server_address)
                connected = True
            except Exception as e:
                debug("Socket server failed to connect to {}, message: {}".format(server_ip,e.message),DEBUG_INTERFACE)
                debug("Retrying...",DEBUG_INTERFACE)
                time.sleep(1)
        return sock


class SocketServerInterface(BaseSocketInterface):
    """
    interfacing to client as tcp server
    """
    _name = "TCP Client Interface"

    def __init__(self,ip=None,port=None):
        super(SocketServerInterface,self).__init__(ip,port)

    def _connect(self,server_ip,server_port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (server_ip, server_port)
        sock.bind(server_address)
        # listening for connections
        sock.listen(1)
        connection, self._client_addr = sock.accept()
        return connection