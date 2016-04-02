import thread
import time
import Queue
import os
from robot import Algo, Map
from mock_android import AndroidInterface
from mock_arduino import ArduinoInterface


class Main:
    def __init__(self):
        #Initialize the fucking bluetooth
        # os.system("sudo hciconfig hci0 piscan")

        #Initialize Queues
        self.toAndroid = Queue.Queue(maxsize=0)
        self.toArduino = Queue.Queue(maxsize=0)
        self.toAlgo = Queue.Queue(maxsize=0)

        self.android = AndroidInterface()
        self.arduino = ArduinoInterface()

    def connectAndroid(self):
        connected = self.android.connect()
        while not connected:
            connected = self.android.connect()

    def connectArduino(self):
        connected = self.arduino.connect()
        while not connected:
            connected = self.arduino.connect()

    def activateAlgo(self, algoQ, arduinoQ, androidQ):
        algo = Algo()
        while 1:
            if not algoQ.empty():
                val = algoQ.get_nowait()
                if algo.explore_done and algo.enter_goal:
                    arduinoQ.put_nowait("CF")
                    break
                if algo.in_start_zone() and algo.enter_goal:
                    arduinoQ.put_nowait("CF")
                    while not algo.commands.empty():
                        print(algo.commands.get_nowait())
                    algo.explore_done = True

                if val == "M":
                    result = algo.move_forward()
                    print("robot mved")
                    print (result)
                elif val == "R":
                    result = algo.turn_right()
                elif val == "L":
                    result = algo.turn_left()
                elif val == "B":
                    result = algo.turn_back()

                elif (val == "SE" and not algo.explore_start):
                    result = algo.explore()
                    arduinoQ.put_nowait(result)

                elif val == "SF":
                    algo.fast()
                    while not algo.commands.empty() and not algo.enter_goal:
                        arduinoQ.put_nowait(algo.commands.get_nowait())

                elif len(val.split(',')) == 6:
                    result = algo.update_map(val)
                    print "algo return to bt to update map", result
                    androidQ.put_nowait(result)
                algo.map.print_map()

# sending data to android from queue
    def btWrite(self, androidQ):
        while 1:
            if not androidQ.empty():
                val = androidQ.get_nowait()
                self.android.write(val)

    # reading android value, send data to algo.
    def btRead(self, algoQ):
        while 1:
            val = self.android.read()
            if val is not None:
                 algoQ.put_nowait(val)

    #sending data to arduino from arduino msg queue.
    def arduinoWrite(self, arduinoQ):
        while 1:
            if not arduinoQ.empty():
                val = arduinoQ.get_nowait()
                self.arduino.write(val)

    #reading data from arduino to ALGO & android.
    def arduinoRead(self, algoQ):
        while 1:
            val = self.arduino.read()
            if val is not None:
                algoQ.put_nowait(val)

    #starting all thread.
    def start_threads(self):
        try:
            thread.start_new_thread(self.btRead, (self.toAlgo,))
            time.sleep(0.5)
            thread.start_new_thread(self.btWrite, (self.toAndroid,))
            thread.start_new_thread(self.arduinoWrite, (self.toArduino,))
            thread.start_new_thread(self.arduinoRead, (self.toAlgo,))
            thread.start_new_thread(self.activateAlgo, (self.toAlgo, self.toArduino, self.toAndroid))

        except Exception, e:
            print "RPI--Cannot start threads: %s" % str(e)
        while 1:
            pass

if "name == __main__":
    test = Main()
    test.connectArduino()
    # test.connectPC()
    test.connectAndroid()
    test.start_threads()
