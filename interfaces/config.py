"""
settings to be used in all programs in the package
"""

# for mock server communication
MOCK_SERVER_ADDR = "192.168.1.1"
# MOCK_SERVER_ADDR = "localhost"
ANDROID_SERVER_PORT = 9039  # server port on Rpi to serve Android
ARDUINO_SERVER_PORT = 9029
PC_SERVER_PORT = 9020

# for real communication
SER_BAUD = 115200
SER_PORT = "/dev/ttyACM"
N7_MAC = "08:60:6E:A5:A5:86"
BT_UUID = "00001101-0000-1000-8000-00805F9B34FB"
BT_PORT = 4

# device labels
VALID_LABELS = ANDROID_LABEL, ARDUINO_LABEL, PC_LABEL = "android","arduino","pc"
CMD_SOURCES = [ANDROID_LABEL,PC_LABEL]
