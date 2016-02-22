"""
This is the script to start running the system
Run main() to start running
"""

from Queue import Queue
import thread

from interfaces import *
from control import CentralController

def write_to_interface(from_queue,interface):
    "thread task for writing to android,pc,arduino"
    while(True):
        if (not from_queue.empty()):
            val = from_queue.get_nowait()
            interface.write(val)

def read_from_interface(to_queue,interface):
    "thread task for reading from android, arduino"
    while(True):
        val = interface.read()
        if (val):to_queue.put_nowait(val)

def connect_interfaces(interfaces):
    "connect a list of interfaces"
    for interface in interfaces:
        interface.connect()

def main():
    "init and start the system"
    # init all queues
    to_android = Queue(maxsize=0) # output
    to_pc = Queue(maxsize=0) # output
    to_arduino = Queue(maxsize=0) # output
    to_control = Queue(maxsize=0) # for processing
    # init all interfaces
    pc_interface = get_pc_interface()
    android_interface = get_android_interface()
    arduino_interface = get_arduino_interface()
    connect_interfaces([pc_interface,android_interface,arduino_interface])
    # start output threads
    #thread.start_new_thread(write_to_interface,(to_pc,pc_interface,))
    thread.start_new_thread(write_to_interface,(to_android,android_interface,))
    thread.start_new_thread(write_to_interface,(to_arduino,arduino_interface,))
    # start input threads
    thread.start_new_thread(read_from_interface,(to_control,arduino_interface,))
    thread.start_new_thread(read_from_interface,(to_control,android_interface,))
    controller = CentralController(input_q=to_control,cmd_out_q=to_arduino,data_out_qs=[to_pc,to_android])
    controller.control_task()



main()