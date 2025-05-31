import socket
import base64
import hashlib
import json
import time
from logger import log_it
from config import Config

def handshake(conn):
    try:
        request = conn.recv(1024).decode()
    except Exception as e:
        log_it("e", f"Failed to receive handshake data: {e}")
        return False

    key = None
    for line in request.split("\r\n"):
        if "Sec-WebSocket-Key" in line:
            key = line.split(": ")[1]
            break
    if not key:
        log_it("e", "WebSocket handshake failed: no Sec-WebSocket-Key")
        return False

    response_key = base64.b64encode(
        hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()
    ).decode()
    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {response_key}\r\n\r\n"
    )
    try:
        conn.send(response.encode())
        log_it("i", f"Handshake successful with {conn.getpeername()}")
        return True
    except Exception as e:
        log_it("e", f"Failed to send handshake response: {e}")
        return False

def send_ping():
    while Config.WEBSOCKET_SERVER_RUNNING:
        time.sleep(30)
        for client in Config.WEBSOCKET_CLIENT.copy():
            try:
                ping_frame = bytearray([0x89, 0x00])
                client.send(ping_frame)
                log_it("d", f"Sent ping to {client.getpeername()}")
            except (OSError, ConnectionResetError, BrokenPipeError) as e:
                log_it("i", f"Removing client {client.getpeername()} due to error: {e}")
                try:
                    client.close()
                except Exception:
                    pass
                if client in Config.WEBSOCKET_CLIENT:
                    Config.WEBSOCKET_CLIENT.remove(client)

def send_message(message):
    for client in Config.WEBSOCKET_CLIENT.copy():
        try:
            encoded_msg = message.encode('utf-8')
            length = len(encoded_msg)
            if length <= 125:
                header = bytearray([0x81, length])
            elif length <= 65535:
                header = bytearray([0x81, 126]) + length.to_bytes(2, byteorder='big')
            else:
                header = bytearray([0x81, 127]) + length.to_bytes(8, byteorder='big')

            data = header + encoded_msg
            log_it("d", f"Sending message to {client.getpeername()}: {message}")
            client.send(data)
        except (OSError, ConnectionResetError, BrokenPipeError) as e:
            log_it("e", f"Client {client.getpeername()} disconnected or errored: {e}")
            if client in Config.WEBSOCKET_CLIENT:
                Config.WEBSOCKET_CLIENT.remove(client)

def ws_broadcast_msg(msg):
    if not Config.WEBSOCKET_SERVER_RUNNING:
        log_it("e", "WebSocket server is not running")
        return
    if not Config.WEBSOCKET_CLIENT:
        log_it("e", "No clients connected to WebSocket server")
        return
    message = json.dumps({"type": "stats_update", "data": msg})
    send_message(message)

def client_handler(conn):
    Config.WEBSOCKET_CLIENT.append(conn)
    log_it("i", f"Client connected: {conn.getpeername()}")
    try:
        while Config.WEBSOCKET_SERVER_RUNNING:
            time.sleep(1)
    except Exception as e:
        log_it("e", f"Error in client handler for {conn.getpeername()}: {e}")
    finally:
        if conn in Config.WEBSOCKET_CLIENT:
            Config.WEBSOCKET_CLIENT.remove(conn)
        try:
            conn.close()
        except Exception:
            pass
        log_it("i", f"Client disconnected: {conn.getpeername()}")

def start_ws_server(port):
    Config.WEBSOCKET_SERVER_RUNNING = True

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", port))
    server.listen(5)
    log_it("i", f"WebSocket server started on port {port}")

    Config.THREADPOOL.submit(send_ping)

    try:
        while Config.WEBSOCKET_SERVER_RUNNING:
            try:
                conn, addr = server.accept()
                if handshake(conn):
                    Config.THREADPOOL.submit(client_handler, conn)
                    ws_broadcast_msg(f"{addr[0]} connected to WebSocket server!")
                else:
                    log_it("e", f"Handshake failed for connection from {addr}")
                    conn.close()
            except Exception as e:
                log_it("e", f"Error accepting connection: {e}")
    finally:
        Config.WEBSOCKET_SERVER_RUNNING = False
        for client in Config.WEBSOCKET_CLIENT:
            try:
                client.close()
            except Exception:
                pass
        Config.WEBSOCKET_CLIENT.clear()
        server.close()
        log_it("i", "WebSocket server stopped")
