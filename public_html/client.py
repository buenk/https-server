"""
Lab 2B - Multiple Sockets / Chat Room (Client)
DESCRIPTION: This file contains the implementation of a chat client. The client
is kept as dumb as possible, the server has to do all the work. The client will
try to connect to the address (127.0.0.1, 12345) unless told otherwise using
the --port and --ip flags.
"""

from threading import Thread
from gui import MainWindow
import socket
import sys
import select


class ChatClient(Thread):
    def __init__(self, port, ip, window):
        """
        port: port to connect to.
        cert: public certificate (task 3)
        ip: IP to bind to (task 3)
        """
        super().__init__()

        self.window = window

        self.wake_socket = self.window.wake_thread

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.connect((ip, port))

        self.socket = s

    def run(self):
        """In this method we listen for incoming messages and process them. We
        also listen for the wake socket, since the program should be closed
        when this socket becomes readable.
        """

        while not self.window.quit_event.is_set():
            inputs = [self.socket, self.wake_socket]
            readable, _, _ = select.select(inputs, [], inputs)

            for s in readable:
                if s is self.socket:
                    data = self.socket.recv(1024)

                    if data:
                        self.window.writeln(data.decode("UTF-8"))
                    else:
                        self.window.writeln("The server is down! Close the " + "program.")
                        self.window.stop()

                if s is self.wake_socket:
                    print("Closing application!")

    def text_entered(self, line):
        """This method is called whenever the user wants to send data, so we
        use the socket to do just that.
        """

        self.socket.sendall(line.encode("UTF-8"))


# Command line argument parser.
if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()

    p.add_argument("--port", help="port to connect to", default=12345, type=int)
    p.add_argument("--ip", help="IP to connect to", default="127.0.0.1", type=str)
    args = p.parse_args(sys.argv[1:])

    w = MainWindow()
    client = ChatClient(args.port, args.ip, w)
    w.set_client(client)
    client.start()
    w.start()
