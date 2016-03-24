from interfaces.mock import MockAndroidInterface

def main():
    interface = MockAndroidInterface()
    interface.connect()
    while(True):
        data = interface.read()
        if (data):
            print("received: " + str(data))

main()
