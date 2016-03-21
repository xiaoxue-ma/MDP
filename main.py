"""
This is the script to start running the system
Run main() to start running
"""

from Queue import Queue
import thread
import threading

from common.debug import debug,DEBUG_IO_QUEUE
from interfaces.config import ARDUINO_LABEL,ANDROID_LABEL,PC_LABEL
from interfaces import *
from fsm.control import CentralController


def write_to_interface(from_queue, interface):
    """thread task for writing to android,pc,arduino"""
    while True:
        if (not from_queue.empty()) and interface.is_ready():
            val = from_queue.get_nowait()
            debug("get {} from queue to write".format(val),DEBUG_IO_QUEUE)
            interface.write(val)


def read_from_interface(to_queue, interface,label):
    """thread task for reading from android, arduino"""
    while True:
        if (interface.is_ready()):
            val = interface.read()
            if val:
                debug("get {} from interface to enqueue".format(val),DEBUG_IO_QUEUE)
                to_queue.put_nowait((label,val))


def connect_interfaces(interfaces):
    """connect a list of interfaces"""
    for interface in interfaces:
        t = threading.Thread(target=interface.connect)
        t.daemon = True
        t.start()


def main(use_mock_arduino=False):
    """init and start the system"""
    # init all queues
    to_android = Queue(maxsize=0)  # output
    to_pc = Queue(maxsize=0)  # output
    to_arduino = Queue(maxsize=0)  # output
    to_control = Queue(maxsize=0)  # for processing
    # init all interfaces
    pc_interface = get_pc_interface()
    android_interface = get_android_interface()
    arduino_interface = get_arduino_interface()
    # run mock arduino
    if (use_mock_arduino):
        from simulators.controllers import ArduinoController
        from common.amap import MapRef
        from common.robot import RobotRef
        arduino_mock = ArduinoController(map_ref=MapRef(),robot_ref=RobotRef())
        thread.start_new_thread(arduino_mock.run,())
    connect_interfaces([pc_interface, arduino_interface,android_interface])
    # start output threads
    thread.start_new_thread(write_to_interface,(to_pc,pc_interface,))
    thread.start_new_thread(write_to_interface, (to_android, android_interface,))
    thread.start_new_thread(write_to_interface, (to_arduino, arduino_interface,))
    # start input threads
    thread.start_new_thread(read_from_interface, (to_control, arduino_interface,ARDUINO_LABEL))
    thread.start_new_thread(read_from_interface, (to_control, android_interface,ANDROID_LABEL))
    thread.start_new_thread(read_from_interface, (to_control, pc_interface,PC_LABEL))
    controller = CentralController(input_q=to_control, cmd_out_q=to_arduino, data_out_qs=[to_pc, to_android])
    controller.control_task()

use_mock_arduino = raw_input("use mock arduino?[y/n]")
if (use_mock_arduino=="y"):
    main(use_mock_arduino=True)
else:
    main()