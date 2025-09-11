"""
Lab 2 - Multiple Sockets / Chat Room (Server)
NAME:
STUDENT ID:
DESCRIPTION:
"""


def serve(port, cert, key):
    """
    Chat server entry point.
    port: The port to listen on.
    cert: The server public certificate.
    key: The server private key.
    """
    pass


# Command line parser.
if __name__ == "__main__":
    import sys
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--port", help="port to listen on", default=12345, type=int)
    p.add_argument("--cert", help="server public cert", default="public_html/cert.pem")
    p.add_argument("--key", help="server private key", default="key.pem")
    args = p.parse_args(sys.argv[1:])
    serve(args.port, args.cert, args.key)
