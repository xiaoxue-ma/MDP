"""
Set of interfaces for software simulation
"""
import socket

from common import *
from base import Interface

class MockPCInterface(Interface):

    def connect(self):
        "create a gui window"
        pass

    def read(self):
        return "mock data"

class MockAndroidInterface(Interface):

    _name = ANDROID_LABEL

    def _get_server_port(self):
        return ANDROID_SERVER_PORT


class MockArduinoInterface(Interface):

    _name = ARDUINO_LABEL

    def _get_server_port(self):
        return ARDUINO_SERVER_PORT
