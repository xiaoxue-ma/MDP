from Tkinter import *
from simulators.android import ClientSimulationApp
from simulators.controllers import PCController

class PCSimulationApp(ClientSimulationApp):
    def get_controller_class(self):
        return PCController

def main():
    window = Tk()
    app = PCSimulationApp(root=window)
    window.title("PC")
    window.mainloop()

if __name__=="__main__":
    main()