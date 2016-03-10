"""
settings to be used in all programs in the package
"""



# for server communication
MOCK_SERVER_ADDR = "192.168.1.1"#"172.22.164.11"
ANDROID_SERVER_PORT = 9080 # server port on Rpi to serve Android
ARDUINO_SERVER_PORT = 9010
PC_SERVER_PORT = 9020

# for communication format
SENSOR_READING_DELIMITER = ","
SENSOR_READING_FORMAT = ("{}"+SENSOR_READING_DELIMITER)*4+"{}" # for arduino to send to rpi, front_mid,front_left,front_right, left, right
ANDROID_LABEL = "android"
ARDUINO_LABEL = "arduino"
PC_LABEL = "pc"

# Rpi only accepts commands from android and pc
CMD_SOURCES = [ANDROID_LABEL,PC_LABEL]
