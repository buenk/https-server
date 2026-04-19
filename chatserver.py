"""
Lab 2 - Multiple Sockets / Chat Room (Server)
NAME: W.E. Buenk
STUDENT ID: 15817814
DESCRIPTION: This is an object oriented version of a chat server that handles
multiple client connections simultaneously. The server supports various
commands like changing nicknames, whispering, listing users, and kicking
users from the chat.
"""

import socket
import select
from datetime import datetime
import random


class ChatServer:
    """
    A chat server that handles multiple client connections and supports various
    chat commands for communication between users.

    Attributes:
        host (str): Host IP to bind to.
        port (int): TCP port number.
        cert (str): Path to the server certificate file.
        key (str): Path to the server private key file.
        commands (dict): Dictionary mapping command strings to handler methods.
        inputs (list): List of sockets to monitor for incoming data.
    """

    def __init__(self, host, port, cert, key):
        """
        Initialize the chat server with host, port, and SSL certificate
        information.

        Args:
            host (str): Host IP to bind to.
            port (int): TCP port number.
            cert (str): Path to the server certificate file.
            key (str): Path to the server private key file.
        """

        self.host = host
        self.port = port
        self.cert = cert
        self.key = key
        self.commands = {
            "/say": self._handle_say,
            "/nick": self._handle_nick,
            "/whisper": self._handle_whisper,
            "/list": self._handle_list,
            "/help": self._handle_help,
            "/?": self._handle_help,
            "/whois": self._handle_whois,
            "/kick": self._handle_kick,
        }
        self.inputs = []

    def _format_message_with_timestamp(self, message):
        """
        Helper function to format messages with a timestamp prefix.

        Args:
            message (str): The message to format.

        Returns:
            str: The message prefixed with timestamp in [hh:mm:ss] format.
        """

        timestamp = datetime.now().strftime("[%H:%M:%S]")
        return f"{timestamp} {message}"

    def start(self):
        """
        Start the chat server by opening the server socket and listening for
        client connections using select for multiplexing.
        """

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(1)

        self.inputs = [server_socket]
        clients = {}

        while True:
            readable, _, _ = select.select(self.inputs, [], [])

            for s in readable:
                if s is server_socket:
                    self._handle_join(s, clients)

                else:
                    nickname = clients[s]["nickname"]

                    data = s.recv(1024).decode("utf-8")
                    if data:
                        if data.startswith("/"):
                            parts = data.strip().split(" ", 2)
                            cmd = parts[0]
                            args = parts[1:]

                            if cmd in self.commands:
                                self.commands[cmd](s, clients, args)
                        else:
                            message = data.strip()
                            formatted_msg = f"{nickname}: {message}\n"
                            msg = self._format_message_with_timestamp(
                                formatted_msg
                            )
                            self._broadcast_message(clients, msg)

                        pass
                    else:
                        self._handle_leave(s, clients)

    def _handle_say(self, s, clients, args):
        """
        Handle the /say command to broadcast a message to all clients.

        Args:
            s (socket): The client socket that sent the command.
            clients (dict): Dictionary of connected clients.
            args (list): List of arguments from the command.
        """

        nickname = clients[s]["nickname"]
        message = " ".join(args).strip() if args else ""
        msg = self._format_message_with_timestamp(f"{nickname}: {message}\n")
        self._broadcast_message(clients, msg)

    def _handle_nick(self, s, clients, args):
        """
        Handle the /nick command to change a user's nickname.

        Args:
            s (socket): The client socket that sent the command.
            clients (dict): Dictionary of connected clients.
            args (list): List of arguments from the command.
        """

        nickname = clients[s]["nickname"]
        new_name = args[0]
        if self.nickname_exists(clients, new_name):
            msg = f"username {new_name} already in use\n"
            s.sendall(msg.encode("utf-8"))
        else:
            formatted_msg = f"user {nickname} changed name to {new_name}\n"
            msg = self._format_message_with_timestamp(formatted_msg)
            clients[s]["nickname"] = new_name

            self._broadcast_message(clients, msg)

    def _handle_whisper(self, s, clients, args):
        """
        Handle the /whisper command to send a private message to another user.

        Args:
            s (socket): The client socket that sent the command.
            clients (dict): Dictionary of connected clients.
            args (list): List of arguments from the command.
        """

        if len(args) < 2:
            s.sendall("usage: /whisper <nick> <message>\n".encode("utf-8"))
            return

        sender_nick = clients[s]["nickname"]
        receiver_nick = args[0]
        message = " ".join(args[1:]).strip()

        target_socket = None
        for other_socket, info in clients.items():
            if info["nickname"] == receiver_nick:
                target_socket = other_socket
                break

        if target_socket:
            whisper_msg = f"whisper to {receiver_nick}: {message}\n"
            s.sendall(
                self._format_message_with_timestamp(whisper_msg).encode(
                    "utf-8"
                )
            )
            whisper_recv_msg = f"{sender_nick} whispers: {message}\n"
            target_socket.sendall(
                self._format_message_with_timestamp(whisper_recv_msg).encode(
                    "utf-8"
                )
            )
        else:
            s.sendall(f"user {receiver_nick} not found\n".encode("utf-8"))

    def _handle_list(self, s, clients, args):
        """
        Handle the /list command to show all connected users with their
        addresses.

        Args:
            s (socket): The client socket that sent the command.
            clients (dict): Dictionary of connected clients.
            args (list): List of arguments from the command.
        """

        body = ""
        for info in clients.values():
            body += f"    {info['nickname']} {info['address']}\n"

        # Add one timestamp to the whole block
        msg = self._format_message_with_timestamp(body.strip("\n"))
        s.sendall((msg + "\n").encode("utf-8"))

    def _handle_whois(self, s, clients, args):
        """
        Handle the /whois command to show the IP address of a specific user.

        Args:
            s (socket): The client socket that sent the command.
            clients (dict): Dictionary of connected clients.
            args (list): List of arguments from the command.
        """

        if len(args) < 1:
            s.sendall("usage: /whois <nick>\n".encode("utf-8"))
            return

        target = args[0]
        for info in clients.values():
            if info["nickname"] == target:
                address = info["address"]
                msg = f"{target} has address {address}\n"
                s.sendall(
                    self._format_message_with_timestamp(msg).encode("utf-8")
                )
                return

        s.sendall(f"user {target} not found\n".encode("utf-8"))

    def _handle_kick(self, s, clients, args):
        """
        Handle the /kick command to remove a user from the chat room.

        Args:
            s (socket): The client socket that sent the command.
            clients (dict): Dictionary of connected clients.
            args (list): List of arguments from the command.
        """

        if len(args) < 1:
            s.sendall("usage: /kick <nick>\n".encode("utf-8"))
            return

        kicked_nick = args[0].strip()
        kicker_nick = clients[s]["nickname"]
        target_socket = None
        for other_socket, info in clients.items():
            if info["nickname"] == kicked_nick:
                target_socket = other_socket
                break

        if target_socket:
            msg = f"has been kicked by {kicker_nick}\n"
            self._disconnect(target_socket, clients, msg)

        else:
            s.sendall(f"user {kicked_nick} not found\n".encode("utf-8"))

    def _handle_help(self, s, clients, args):
        """
        Handle the /help command to display available chat commands.

        Args:
            s (socket): The client socket that sent the command.
            clients (dict): Dictionary of connected clients.
            args (list): List of arguments from the command (unused).
        """

        help_text = (
            "available commands:\n"
            "/nick <new_nick>       - change your nickname\n"
            "/say <text>            - broadcast a chat message\n"
            "/whisper <nick> <text> - send a private message\n"
            "/list                  - show list of connected users\n"
            "/whois <nick>          - show info about a user\n"
            "/kick <nick>           - kick a user from the chatroom\n"
            "/help or /?            - show this help message\n"
        )

        s.sendall(help_text.encode("utf-8"))

    def _handle_join(self, s, clients):
        """
        Handle a new client connection by accepting the socket and assigning a
        guest name.

        Args:
            s (socket): The server socket accepting connections.
            clients (dict): Dictionary of connected clients.
        """

        client_socket, client_address = s.accept()
        self.inputs.append(client_socket)

        new_name = self._generate_guest_name(clients)

        # Store the client data
        clients[client_socket] = {
            "nickname": new_name,
            "address": client_address[0],
        }

        join_msg = (
            f"{str(client_address[0])} connected with name {new_name}\n"
        )
        msg = self._format_message_with_timestamp(join_msg)
        for other_socket, _ in clients.items():
            if other_socket is not client_socket:
                other_socket.sendall(msg.encode("utf-8"))

    def _generate_guest_name(self, clients):
        """
        Generate a unique guest nickname for new clients.

        Args:
            clients (dict): Dictionary of connected clients.

        Returns:
            str: A unique guest nickname in format "guest_XXXX".
        """

        while True:
            rand_id = random.randint(1000, 9999)
            nickname = f"guest_{rand_id}"

            # Make sure no existing client has the name already.
            if not any(
                info["nickname"] == nickname for info in clients.values()
            ):
                return nickname

    def _handle_leave(self, s, clients):
        """
        Handle client disconnection by calling disconnect with default reason.

        Args:
            s (socket): The client socket that disconnected.
            clients (dict): Dictionary of connected clients.
        """

        self._disconnect(s, clients, "disconnected")

    def _disconnect(self, s, clients, reason_msg=None):
        """
        Disconnect a client socket and notify other clients of the
        disconnection.

        Args:
            s (socket): The client socket to disconnect.
            clients (dict): Dictionary of connected clients.
            reason_msg (str, optional): Reason for disconnection.
        """

        nickname = clients[s]["nickname"]

        if s in self.inputs:
            self.inputs.remove(s)
        del clients[s]

        s.close()

        if reason_msg:
            disconnect_msg = f"{nickname} {reason_msg}\n"
            formatted = self._format_message_with_timestamp(disconnect_msg)
            self._broadcast_message(clients, formatted, exclude=s)

    def nickname_exists(self, clients, nickname):
        """
        Check if a nickname is already in use by any connected client.

        Args:
            clients (dict): Dictionary of connected clients.
            nickname (str): The nickname to check.

        Returns:
            bool: True if nickname exists, False otherwise.
        """

        for info in clients.values():
            if info["nickname"] == nickname:
                return True
        return False

    def _broadcast_message(self, clients, msg, exclude=None):
        """
        Broadcast a message to all connected clients.

        Args:
            clients (dict): Dictionary of connected clients.
            msg (str): The message to broadcast.
        """

        for other_socket, _ in clients.items():
            if exclude is not None and other_socket is exclude:
                continue
            try:
                other_socket.sendall(msg.encode("utf-8"))
            except OSError:
                # socket already closed
                pass


def serve(port, cert, key):
    """
    The entry point of the chat server.

    Args:
        port (int): The port to listen to.
        cert (str): The server public certificate file path.
        key (str): The server private key file path.
    """

    server = ChatServer("127.0.0.1", port, cert, key)
    server.start()


# Command line parser.
if __name__ == "__main__":
    import sys
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument(
        "--port", help="port to listen on", default=12345, type=int
    )
    p.add_argument(
        "--cert", help="server public cert", default="public_html/cert.pem"
    )
    p.add_argument("--key", help="server private key", default="key.pem")
    args = p.parse_args(sys.argv[1:])
    serve(args.port, args.cert, args.key)
