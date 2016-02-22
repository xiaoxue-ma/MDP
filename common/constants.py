"""
constants to be used in all programs in the package
"""

# for server communication
MOCK_SERVER_ADDR = "localhost"
ANDROID_SERVER_PORT = 9000 # server port on Rpi to serve Android
ARDUINO_SERVER_PORT = 9010
PC_SERVER_PORT = 9020

# for communication format
SENSOR_READING_DELIMITER = ","
SENSOR_READING_FORMAT = ("{}"+SENSOR_READING_DELIMITER)*4+"{}" # for arduino to send to rpi, front_mid,front_left,front_right, left, right
ANDROID_LABEL = "android"
ARDUINO_LABEL = "arduino"
PC_LABEL = "pc"
