"""
Set of interfaces for software simulation
"""
import socket
from threading import Lock
from interfaces.config import *
from base import SocketServerInterface


class MockPCInterface(SocketServerInterface):
    _name = PC_LABEL + "interface" # hardcoded to make pc act same as android
    _server_ip = MOCK_SERVER_ADDR
    _server_port = PC_SERVER_PORT
    _write_delay = 0.1

class MockAndroidInterface(SocketServerInterface):
    _name = ANDROID_LABEL + "interface"
    _server_ip = MOCK_SERVER_ADDR
    _server_port = ANDROID_SERVER_PORT
    _write_delay = 0.2

class MockArduinoInterface(SocketServerInterface):
    _name = ARDUINO_LABEL + "interface"
    _server_ip = MOCK_SERVER_ADDR
    _server_port = ARDUINO_SERVER_PORT
    _write_delay = 0.6