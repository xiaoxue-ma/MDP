from Tkinter import *
import socket
from thread import start_new_thread
import time

class PCSimulationApp():

    _text = None

    def __init__(self,root):
        # create Frame
        self._text = Text(master=root,height=10)
        self._text.pack()
        # start server
        start_new_thread(self.start_server,())

    def start_server(self):
        # set up server socket
        time.sleep(1)
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        server_address = ('localhost',9000)
        sock.bind(server_address)
        self.show_status("server started...")
        # listening for connections
        while True:
            sock.listen(1)
            connection,client_addr = sock.accept()
            self.show_status("accept client: " + str(client_addr))
            start_new_thread(self.serve_connection,(connection,))

    def serve_connection(self,conn):
        "communicate over one connection"
        while True:
            data =conn.recv(1024)
            self.show_status("received data: " + str(data))
            reply = "Pc has received " + str(data)
            conn.sendall(reply)

    def show_status(self,msg):
        self._text.insert(END,msg+"\n")


def main():
    window = Tk()
    app = PCSimulationApp(root=window)
    window.title("PC")
    window.mainloop()

main()