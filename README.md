# Lab 2 — HTTP Server & Chat Room

A two-part networking assignment written from scratch in Python, covering raw TCP socket programming, the HTTP protocol, and multi-client server design.

---

## Part A — HTTP Server (`httpserver.py`)

A single-socket HTTP/1.x server that serves static files from `public_html/`. Handles `GET` requests and returns `404` or `501` for missing resources and unsupported methods. Tracks page visits with an HTTP cookie (`page-counter`), and constructs all request/response headers manually.

```sh
python httpserver.py --port 8080
```

## Part B — Chat Room (`chatserver.py` + `client.py`)

A multi-client TCP chat server using `select` for I/O multiplexing (no threads server-side). Clients connect via a `tkinter` GUI and support commands like `/nick`, `/whisper`, `/kick`, `/list`, and `/whois`. Messages are timestamped and broadcast to all connected users.

```sh
python chatserver.py --port 12345
python public_html/client.py --ip 127.0.0.1 --port 12345
```

---

## Code Design

Both servers follow an object-oriented design where responsibilities are clearly separated. `HTTPServer` handles the socket lifecycle while `HTTPRequestHandler` deals purely with parsing and response generation. Similarly, `ChatServer` owns the connection loop and delegates each command to its own dedicated method via a command dispatch table (`dict` mapping command strings to handler methods), making it easy to extend with new commands. 

## Technologies & Concepts Learned

- **TCP socket programming** — raw socket creation, binding, listening, and data transfer using Python's `socket` module
- **HTTP/1.x protocol** — manual parsing of requests and construction of responses (status line, headers, body)
- **HTTP cookies** — `Set-Cookie` / `Cookie` headers for persistent client-side state
- **I/O multiplexing** — `select.select()` to handle multiple clients concurrently without threads
- **Multithreading** — `threading.Thread` in the client to run socket I/O alongside the GUI
- **SSL/TLS** — certificate and private key integration for encrypted chat connections
- **tkinter** — building a simple GUI chat client with a scrolled text log and input field
- **HTML / CSS / JavaScript** — static frontend with a JS cookie reader for the visit counter
- **OOP** — clean class-based design (`HTTPServer`, `HTTPRequestHandler`, `ChatServer`, `ChatClient`)
