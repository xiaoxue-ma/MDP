"""
set of real device communication interfaces
"""
import serial,time
from base import Interface
from config import *
from bluetooth import *

class PCInterface(Interface):
    pass


class Arduino(Interface):

    def __init__(self):
        self.baudrate = BAUD
        self.ser = 0

    def connect(self):
        #connect to serial port
        try:
            print "Trying to connect to Arduino..."
            self.ser = serial.Serial(SER_PORT0,self.baudrate, timeout=3)
            time.sleep(1)

            if(self.ser != 0):
                print "Connected to Arduino!"
                self.read()
                return 1

        except Exception, e:
            self.ser = serial.Serial(SER_PORT1,self.baudrate,timeout=3)
            return 1

    def write(self,msg):
        try:
            self.ser.write(msg + "|") #write msg with | as end of msg
        except Exception, e:
            print "Arduino write exception: %s" %str(e)

    def read(self):
        try:
            msg = self.ser.readline() #read msg from arduino sensors
            return msg
        except Exception, e:
            print "Arduino read exception: %s" %str(e)


class Android(Interface):

    def connect(self):
        try:
            self.server_sock=BluetoothSocket( RFCOMM )
            #self.server_sock.allow_reuse_address = True
            #self.server_sock = self.server_socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #self.server_sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            self.server_sock.bind(("",5))
            self.server_sock.listen(5)
            port = self.server_sock.getsockname()[1]

            advertise_service(self.server_sock, "SampleServer",
                                service_id = UUID,
                                service_classes = [ UUID, SERIAL_PORT_CLASS ],
                                profiles = [ SERIAL_PORT_PROFILE ],)

            print "-----------------------------------------"
            print "Waiting connection from RFCOMM channel %d" % port
            self.btsock, client_info = self.server_sock.accept()
            secure = client_info[0]

#            if secure != "08:60:6E:A5:A4:1E":
 #               print "Tablet MAC Address unrecgonized... Disconnecting..."
  #              return 0

            print "Accepted connection from ", client_info
            print "Connected to Android!"
            return 1
        except Exception, e:
            print "Bluetooth connection exception: %s" %str(e)
            try:
                print "%s" %str(x)
                self.btsock.close()
                self.server_sock.close()
            except:
                print "Error"
            return 0

    def disconnect(self):
        try:
            self.btsock.close()
            self.server_sock.close()
        except Exception, e:
            print "Bluetooth disconnection exception: %s" %str(e)

    def reconnect(self):
        connected = 0
        connected = self.connect("00001101-0000-1000-8000-00805F9B34FB")
        while connected == 0:
            print "Attempting reconnection..."
            #self.disconnect()
            time.sleep(1)
            connected = self.connect()

    def write(self,msg):
        try:
            self.btsock.send(msg)
  #          print "Write to Android: %s" %(msg)
        except Exception, e:
            print "Bluetooth write exception: %s" %str(e)
            self.reconnect()

    def read(self):
        try:
            msg = self.btsock.recv(1024)
   #         print "Read from Android: %s" %(msg)
            return (msg)
        except Exception, e:
            print "Bluetooth read exception: %s" %str(e)
            self.reconnect()