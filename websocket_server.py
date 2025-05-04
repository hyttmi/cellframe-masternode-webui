import socket, base64, hashlib, threading
from logger import log_it

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

def send_message(conn, message):
    data = bytearray([0x81, len(message)])
    data.extend(message.encode('utf-8'))
    log_it("d", f"Sending message to {conn.getpeername()}: {message}")
    conn.send(data)

def client_handler(conn):
    clients.append(conn)
    log_it("i", f"Client connected: {conn.getpeername()}")
    try:
        while True:
            pass
    finally:
        clients.remove(conn)
        conn.close()

def find_available_port(start_port, end_port):
    for port in range(start_port, end_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                s.close()
                return port
            except socket.error:
                continue
    return None

def start_ws_server():
    available_port = find_available_port(40000, 42000)
    if available_port is None:
        print("No available ports found in the range 40000-42000, strange that is...")
        return
    server = socket.socket()
    server.bind(("0.0.0.0", available_port))
    server.listen(5)
    log_it("i", f"WebSocket server started on port {available_port}")
    while True:
        conn, _ = server.accept()
        if handshake(conn):
            threading.Thread(target=client_handler, args=(conn,), daemon=True).start()

def broadcast_stats_update(stats):
    message = '{"type": "stats_update", "data": ' + str(stats) + '}'
    for conn in clients:
        try:
            send_message(conn, message)
        except:
            clients.remove(conn)