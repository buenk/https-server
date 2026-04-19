"""
Lab 2 - Single Socket / HTTP Server
NAME: W.E. Buenk
STUDENT ID: 15817814
DESCRIPTION: This is an object oriented version of a HTTP server that serves
static HTML files. This server supports only GET requests.
"""

import socket
import time


class HTTPServer:
    """
    A simple HTTP server that serves static files and cookies.

    Attributes:
        host (str): Host IP to bind to.
        port (int): TCP port number.
        public_html (str): Path to directory with static HTML files.
    """

    def __init__(self, host, port, public_html):
        self.host = host
        self.port = port
        self.public_html = public_html

    def start(self):
        """
        Start the HTTP server by opening the server socket and listening for
        connections.
        """

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(1)

        while True:
            client_socket, address = server_socket.accept()
            self._serve_client(client_socket)

    def _serve_client(self, client_socket):
        """
        Receive data from the client socket and extract the response headers
        and body from the request handler, after which we send back the HTML
        data.

        Args:
            client_socket (socket): The client socket.
        """

        request = client_socket.recv(1024).decode("utf-8")

        request_handler = HTTPRequestHandler(public_html)
        response_headers, body = request_handler.handle(request)

        client_socket.sendall(response_headers.encode("utf-8") + body)
        client_socket.close()


class HTTPRequestHandler:
    """
    Class to handle raw HTML requests and decode them into response headers
    and a body.

    Attributes:
        public_html (str): Path to directory with static HTML files.
    """

    def __init__(self, public_html):
        self.public_html = public_html

    def handle(self, request):
        """
        Parse the raw data of the HTML request and send back the appropriate
        response. The reponse includes a cookie with a counter that says how
        often the page has been visited.

        Args:
            request (str): The raw request data.

        Returns:
            tuple[str, bytes]: The raw HTTP headers string and the body as
            bytes.
        """

        lines = request.split("\r\n")
        method, path, version = lines[0].split(" ")

        headers = {}
        for line in lines[1:]:
            if line == "":
                break
            key, value = line.split(":", 1)
            headers[key.strip()] = value.strip()

        cookie_header = headers.get("Cookie")
        if cookie_header and "page-counter=" in cookie_header:
            page_counter_value = int(cookie_header.split("=")[1]) + 1
        else:
            page_counter_value = 1

        # Handle 501 Early
        if method != "GET":
            return self._not_implemented(version)

        extra_headers = {
            "Set-Cookie": (
                f"page-counter={page_counter_value}; Max-Age=31536000"
            )
        }
        return self._handle_get(version, path, extra_headers)

    def _handle_get(self, version, path, extra_headers=None):
        """
        Generate headers and body for the respone to a GET request.

        Returns:
            tuple[str, bytes]: The raw HTTP headers string and the body as
            bytes.
        """

        if path == "/":
            path = "/index.html"

        # use lstrip to prevent an absolute path
        filepath = os.path.join(public_html, path.lstrip("/"))

        # Handle 404 early
        if not os.path.exists(filepath):
            return self._file_not_found(version)

        return self._generate_response(version, 200, filepath, extra_headers)

    def _not_implemented(self, version):
        """
        Generate headers and body for the not implemented response.

        Returns:
            tuple[str, bytes]: The raw HTTP headers string and the body as
            bytes.
        """

        return self._generate_response(version, 501)

    def _file_not_found(self, version):
        """
        Generate headers and body for the file not found response.

        Returns:
            tuple[str, bytes]: The raw HTTP headers string and the body as
            bytes.
        """

        return self._generate_response(version, 404)

    def _generate_response(
        self, version, code, filepath="", extra_headers=None
    ):
        """
        Generates HTML body and headers based on the type of response being
        sent. This function handles 200, 404 and 501 responses, otherwise an
        error is raised.

        Args:
            version (str): The HTTP version.
            code (int): Status code of the HTTP response to be sent.
            filepath (str): Path to the static HTML file.
            extra_headers (dict): Headers to add to the response.

        Returns:
            tuple[str, bytes]: The raw HTTP headers string and the body as
            bytes.

        Raises:
            ValueError: If the code is 200 but no file path is given.
            NotImplementedError: If an unsupported status code is passed.
        """

        date_header = time.strftime(
            "%a, %d %b %Y %H:%M:%S GMT", time.gmtime()
        )

        if code == 200:
            if filepath == "":
                raise ValueError("filepath is required for 200 OK response")
            with open(filepath, "rb") as f:
                body = f.read()
            status = f"{version} 200 OK\r\n"
        elif code == 404:
            body = b"<h1>404 Not Found</h1>"
            status = f"{version} 404 Not Found\r\n"
        elif code == 501:
            body = b"<h1>501 Not Implemented</h1>"
            status = f"{version} 501 Not Implemented\r\n"
        else:
            raise NotImplementedError(f"Status code {code} not handled")

        response_headers = (
            status
            + f"Date: {date_header}\r\n"
            + "Content-Type: text/html\r\n"
            + f"Content-Length: {len(body)}\r\n"
            + "Connection: close\r\n"
            + "Server: WEB\r\n"
        )

        if extra_headers:
            for key, value in extra_headers.items():
                response_headers += f"{key}: {value}\r\n"

        response_headers += "\r\n"  # Blank line between headers and body

        return response_headers, body


def serve(port, public_html):
    """
    The entry point of the HTTP server.

    Args:
        port (int): The port to listen on.
        public_html (str): The directory where all static files are stored.
    """

    server = HTTPServer("127.0.0.1", port, public_html)
    server.start()


# This the entry point of the script.
# Do not change this part.
if __name__ == "__main__":
    import os
    import sys
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--port", help="port to bind to", default=8080, type=int)
    p.add_argument(
        "--public_html", help="home directory", default="./public_html"
    )
    args = p.parse_args(sys.argv[1:])
    public_html = os.path.abspath(args.public_html)
    serve(args.port, public_html)
