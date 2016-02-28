from abc import ABCMeta, abstractmethod
from thread import start_new_thread
import socket


class BaseNetworkInterface():
    __metaclass__ = ABCMeta

    _buffer = ''  # temporary storage for data received

    RECV_VALUE = 2048  # number of bytes to receive at one time

    def start(self, noblock=False):
        if (noblock):
            start_new_thread(self._internal_start, ())
        else:
            self._internal_start()

    @abstractmethod
    def _internal_start(self):
        pass

    def read(self):
        return self.wrap_data(self._get_io().recv(self.RECV_VALUE))

    def write(self, data):
        self._get_io().sendall(self.unwrap_data(data))

    @abstractmethod
    def _get_io(self):
        """return the io port: socket or connection"""
        pass

    def wrap_data(self, data):
        """override this to preprocess the data received"""
        return data

    def unwrap_data(self, data):
        """override this to postprocess the data to be sent"""
        return data


class SocketServer(BaseNetworkInterface):
    _addr = "localhost"
    _port = 9000
    _connection = None
    _client_addr = None

    def __init__(self, addr, port):
        self._addr = addr
        self._port = port
        self._buffer = []

    def _internal_start(self):
        """thread task"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (self._addr, self._port)
        sock.bind(server_address)
        # listening for connections
        sock.listen(1)
        connection, self._client_addr = sock.accept()
        print("COnnected to client {}".format(self._client_addr))
        self._connection = connection

    def _get_io(self):
        return self._connection

    def get_client_addr(self):
        if not self._client_addr:
            raise Exception("no client yet, this method should only be called after start()")
        return self._client_addr


class SocketClient(BaseNetworkInterface):
    _server_addr = "localhost"
    _server_port = 0
    _sock = None

    RECV_VALUE = 2048  # number of bytes to receive at one time

    def __init__(self, server_addr, server_port):
        self._server_addr = server_addr
        self._server_port = server_port

    def _internal_start(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock = sock
        server_ip = self._server_addr
        server_port = self._server_port
        server_address = (server_ip, server_port)
        sock.connect(server_address)

    def _get_io(self):
        return self._sock
