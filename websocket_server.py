import socket, base64, hashlib, json, time
from logger import log_it
from config import Config, Globals
from thread_launcher import start_thread
from utils import is_port_available

def handshake(conn):
    request = conn.recv(1024).decode()
    key = None
    for line in request.split("\r\n"):
        if "Sec-WebSocket-Key" in line:
            key = line.split(": ")[1]
            break
    if not key:
        return False
    response_key = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {response_key}\r\n\r\n"
    )
    conn.send(response.encode())
    log_it("i", f"Handshake successful with {conn.getpeername()}")
    return True

def send_ping():
    while Globals.WEBSOCKET_SERVER_RUNNING:
        time.sleep(30)  # Ping every 30 seconds
        for client in Globals.WEBSOCKET_CLIENT.copy():
            try:
                ping_frame = bytearray([0x89, 0x00])
                client.send(ping_frame)
                log_it("d", f"Sent ping to {client.getpeername()}")
            except (OSError, ConnectionResetError, BrokenPipeError) as e:
                log_it("i", f"Removing client {client}: {e}")
                log_it("d", f"Current list of clients: {Globals.WEBSOCKET_CLIENT}")
                try:
                    client.close()
                except:
                    pass
                Globals.WEBSOCKET_CLIENT.remove(client)
                log_it("d", f"Client {client} removed. Remaining clients: {Globals.WEBSOCKET_CLIENT}")

def send_message(message):
    for client in Globals.WEBSOCKET_CLIENT.copy():
        try:
            data = bytearray([0x81, len(message)])
            data.extend(message.encode('utf-8'))
            log_it("d", f"Sending message to {client.getpeername()}: {message}")
            client.send(data)
        except (OSError, ConnectionResetError, BrokenPipeError) as e:
            log_it("e", f"Client {client} disconnected or errored: {e}")
            Globals.WEBSOCKET_CLIENT.remove(client)

def start_ws_server(port):
    if port <= 0:
        log_it("e", f"Invalid WebSocket server port: {port}. Must be a positive integer.")
        return
    elif port < 1024 or port > 65535:
        log_it("e", f"Invalid WebSocket server port: {port}. Must be between 1024 and 65535.")
        return
    elif not is_port_available(port):
        log_it("e", f"WebSocket server port {port} is not available.")
        return
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", port))
    server.listen(5)
    Globals.WEBSOCKET_SERVER_RUNNING = True
    log_it("i", f"WebSocket server started on thread")
    start_thread(send_ping)
    log_it("i", "send_ping started on thread")
    while True:
        try:
            conn, _ = server.accept()
            if handshake(conn):
                Globals.WEBSOCKET_CLIENT.append(conn)
                log_it("d", f"New handshake for WebSocket connection. Clients currently connected: {Globals.WEBSOCKET_CLIENT}")
                ws_broadcast_msg(f"{conn.getpeername()[0]} connected to WebSocket server!")
        except Exception as e:
            log_it("e", f"WebSocket server error: {e}")

def ws_broadcast_msg(msg):
    if not Globals.WEBSOCKET_SERVER_RUNNING:
        log_it("e", "WebSocket server is not running")
        return
    if not Globals.WEBSOCKET_CLIENT:
        log_it("e", "No clients connected to WebSocket server")
        return
    message = json.dumps({"type": "stats_update", "data": msg})
    send_message(message)