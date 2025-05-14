import socket, base64, hashlib, threading, json
from logger import log_it
from config import Config
from utils import is_port_available

websocket_server_running = False
clients = []

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

def send_message(message):
    if clients:
        for client in clients:
            data = bytearray([0x81, len(message)])
            data.extend(message.encode('utf-8'))
            log_it("d", f"Sending message to {client.getpeername()}: {message}")
            client.send(data)

def client_handler(conn):
    clients.append(conn)
    log_it("i", f"Client connected: {conn.getpeername()}")
    try:
        while True:
            pass
    finally:
        clients.remove(conn)
        conn.close()

def start_ws_server():
    global websocket_server_running
    available_port = Config.WEBSOCKET_SERVER_PORT
    if not is_port_available(available_port):
        log_it("e", f"WebSocket server port {available_port} is not available")
        return
    server = socket.socket()
    server.bind(("0.0.0.0", available_port))
    server.listen(5)
    websocket_server_running = True
    while True:
        conn, _ = server.accept()
        if handshake(conn):
            threading.Thread(target=client_handler, args=(conn,), daemon=True).start()

def ws_broadcast_msg(msg):
    if not websocket_server_running:
        log_it("e", "WebSocket server is not running")
        return
    if not clients:
        log_it("e", "No clients connected to WebSocket server")
        return
    message = json.dumps({"type": "stats_update", "data": msg})
    send_message(message)
