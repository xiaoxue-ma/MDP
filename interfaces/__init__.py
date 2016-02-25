from mock import *


__all__ = ('get_pc_interface', 'get_arduino_interface', 'get_android_interface',)


# methods for getting interfaces
# change these methods to change the interfaces to be used
def get_pc_interface():
    return MockPCInterface()


def get_arduino_interface():
    return MockArduinoInterface()


def get_android_interface():
    return MockAndroidInterface()