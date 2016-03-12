"""
set of real device communication interfaces
"""
import time

import serial
from bluetooth import *
from base import Interface
from common.pmessage import PMessage,ValidationException
from common.debug import debug,DEBUG_INTERFACE,DEBUG_VALIDATION
from interfaces.config import *


TO_SER = dict({PMessage.M_MOVE_FORWARD: "0", PMessage.M_TURN_RIGHT: "1", PMessage.M_TURN_LEFT: "2",
               PMessage.M_TURN_BACK: "3", PMessage.M_START_EXPLORE: "4", PMessage.M_END_EXPLORE: "5",
               PMessage.M_START_FASTRUN: "6", })
FROM_SER = dict({"0": PMessage.M_MOVE_FORWARD, "1": PMessage.M_TURN_RIGHT, "2": PMessage.M_TURN_LEFT,
                 "3": PMessage.M_TURN_BACK, "4": PMessage.M_START_EXPLORE, "5": PMessage.M_END_EXPLORE,
                 "6": PMessage.M_START_FASTRUN, })

class ArduinoInterface(Interface):
    name = ARDUINO_LABEL

    def __init__(self):
        super(ArduinoInterface,self).__init__()
        self.status = False

    def connect(self):
        connected = False
        while(not connected):
            try:
                debug("Trying to connect to arduino...",DEBUG_INTERFACE)
                self.ser = serial.Serial(SER_PORT, SER_BAUD, timeout=3)
                time.sleep(2)
                if self.ser is not None:
                    self.set_ready()
                    debug("SER--Connected to Arduino!",DEBUG_INTERFACE)
                    connected = True
            except Exception, e:
                debug("SER--connection exception: %s" % str(e),DEBUG_INTERFACE)

    def disconnect(self):
        if self.ser.is_open:
            self.ser.close()
            self.set_not_ready()
            debug("SER--Disconnected to Arduino!",DEBUG_INTERFACE)


    def read(self):
        try:
            msg = self.ser.readline()
            if msg != "":
                debug("SER--Read from Arduino: %s" % str(msg),DEBUG_INTERFACE)
                if len(msg) > 1:
                    if msg[0] != 'T':
                        realmsg = PMessage(type=PMessage.T_MAP_UPDATE, msg=msg)
                        return realmsg
                else:
                    msg = msg[0]
                    if msg < '4':
                        realmsg = PMessage(type=PMessage.T_ROBOT_MOVE, msg=FROM_SER.get(msg[0]))
                        return realmsg
        except ValidationException as e:
            debug("validation exception: {}".format(e.message),DEBUG_VALIDATION)
        except Exception, e:
            debug("SER--read exception: %s" % str(e),DEBUG_INTERFACE)
            self.reconnect()

    def write(self, msg):
        try:
            realmsg = TO_SER.get(msg.get_msg())
            if realmsg:
                self.ser.write(realmsg)
                time.sleep(1)
                debug("SER--Write to Arduino: %s" % str(msg),DEBUG_INTERFACE)
        except Exception, e:
            debug("SER--write exception: %s" % str(e),DEBUG_INTERFACE)
            self.reconnect()


class AndroidInterface(Interface):

    name = ANDROID_LABEL
    _write_delay = 1

    def __init__(self):
        super(AndroidInterface,self).__init__()
        self.status = False

    def connect(self):
        connected = False
        while(not connected):
            try:
                self.server_sock = BluetoothSocket(RFCOMM)
                self.server_sock.bind(("", BT_PORT))
                self.server_sock.listen(2)
                port = self.server_sock.getsockname()[1]
                advertise_service(self.server_sock, "SampleServer",
                                  service_id=BT_UUID,
                                  service_classes=[BT_UUID, SERIAL_PORT_CLASS],
                                  profiles=[SERIAL_PORT_PROFILE],
                )
                self.client_sock, client_info = self.server_sock.accept()
                debug("BT--Connected to %s on channel %s" % (str(client_info), str(port)),DEBUG_INTERFACE)
                self.set_ready()
                return True
            except Exception, e:
                debug("BT--connection exception: %s" % str(e),DEBUG_INTERFACE)

    def disconnect(self):
        try:
            self.client_sock.close()
            self.server_sock.close()
            self.set_not_ready()
            debug("BT--Disconnected to Android!",DEBUG_INTERFACE)
        except Exception, e:
            debug("BT--disconnection exception: %s" % str(e),DEBUG_INTERFACE)


    def read(self):
        try:
            msg = self.client_sock.recv(2048)
            debug("BT--Read from Android: %s" % str(msg),DEBUG_INTERFACE)
            return PMessage(json_str=msg)
        except ValidationException as e:
            debug("Validation exception: {}".format(e.message),DEBUG_VALIDATION)
        except Exception, e:
            debug("BT--read exception: %s" % str(e),DEBUG_INTERFACE)
            self.reconnect()


    def write(self, msg):
        try:
            msg = msg.render_msg()
            self.client_sock.send(msg)
            time.sleep(self._write_delay)
            debug("BT--Write to Android: %s" % str(msg),DEBUG_INTERFACE)
        except Exception, e:
            debug("BT--write exception: %s" % str(e),DEBUG_INTERFACE)
