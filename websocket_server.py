import socket, base64, hashlib, json, time
from logger import log_it
from config import Config

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
    while Config.WEBSOCKET_SERVER_RUNNING:
        time.sleep(30)  # Ping every 30 seconds
        for client in Config.WEBSOCKET_CLIENT.copy():
            try:
                ping_frame = bytearray([0x89, 0x00])
                client.send(ping_frame)
                log_it("d", f"Sent ping to {client.getpeername()}")
            except (OSError, ConnectionResetError, BrokenPipeError) as e:
                log_it("i", f"Removing client {client}: {e}")
                try:
                    client.close()
                except:
                    pass
                Config.WEBSOCKET_CLIENT.remove(client)

def send_message(message):
    for client in Config.WEBSOCKET_CLIENT.copy():
        try:
            data = bytearray([0x81, len(message)])
            data.extend(message.encode('utf-8'))
            log_it("d", f"Sending message to {client.getpeername()}: {message}")
            client.send(data)
        except (OSError, ConnectionResetError, BrokenPipeError) as e:
            log_it("e", f"Client {client} disconnected or errored: {e}")
            Config.WEBSOCKET_CLIENT.remove(client)

def client_handler(conn):
    Config.WEBSOCKET_CLIENT.append(conn)
    log_it("i", f"Client connected: {conn.getpeername()}")
    ws_broadcast_msg("Connected to WebSocket server!")
    try:
        while True:
            pass
    finally:
        if conn in Config.WEBSOCKET_CLIENT:
            Config.WEBSOCKET_CLIENT.remove(conn)
        conn.close()

def start_ws_server(port):
    server = socket.socket()
    server.bind(("0.0.0.0", port))
    server.listen(5)
    log_it("i", f"WebSocket server started on port {port}")

    while True:
        conn, _ = server.accept()
        if handshake(conn):
            Config.WEBSOCKET_CLIENT.append(conn)
            ws_broadcast_msg("Connected to WebSocket server!")

def ws_broadcast_msg(msg):
    if not Config.WEBSOCKET_SERVER_RUNNING:
        log_it("e", "WebSocket server is not running")
        return
    if not Config.WEBSOCKET_CLIENT:
        log_it("e", "No clients connected to WebSocket server")
        return
    message = json.dumps({"type": "stats_update", "data": msg})
    send_message(message)
