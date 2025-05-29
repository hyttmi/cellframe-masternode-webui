from logger import log_it
import sys

class LogRedirect:
    def write(self, message):
        if message.strip():
            log_it("e", message.strip())

    def flush(self):
        pass

sys.stderr = LogRedirect()

try:
    from config import Config
    from handlers import request_handler
    from pycfhelpers.node.http.simple import CFSimpleHTTPServer, CFSimpleHTTPRequestHandler
    from run_scheduler import setup_schedules
    from cacher import release_lock, is_locked
    from concurrent.futures import ThreadPoolExecutor
    import traceback
    from websocket_server import start_ws_server, send_ping
    from utils import get_current_config, is_port_available

    executor = ThreadPoolExecutor()

    def http_server():
        try:
            handler = CFSimpleHTTPRequestHandler(methods=["GET", "POST"], handler=request_handler)
            CFSimpleHTTPServer().register_uri_handler(uri=f"/{Config.PLUGIN_URL}", handler=handler)
            log_it("i", "HTTP server started")
        except Exception as e:
            log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())

    def init():
        try:
            current_config  = get_current_config(hide_sensitive_data=True)
            for key, value in current_config.items():
                log_it("d", f"{key}: {value}")
            if is_locked():
                log_it("i", "Cache lock found, releasing it...")
                release_lock()
            executor.submit(http_server)
            log_it("i", "HTTP server started!")
            executor.submit(setup_schedules)
            log_it("i", "Scheduled tasks started!")
            if Config.WEBSOCKET_SERVER_PORT < 1024 or Config.WEBSOCKET_SERVER_PORT > 65535:
                log_it("e", f"Invalid WebSocket server port: {Config.WEBSOCKET_SERVER_PORT}. Must be between 1024 and 65535.")
            elif not is_port_available(Config.WEBSOCKET_SERVER_PORT):
                log_it("e", f"Invalid WebSocket server port {Config.WEBSOCKET_SERVER_PORT}, can't bind the port.")
            else:
                executor.submit(start_ws_server, Config.WEBSOCKET_SERVER_PORT)
                log_it("i", f"WebSocket server started on port {Config.WEBSOCKET_SERVER_PORT}")
                Config.WEBSOCKET_SERVER_RUNNING = True
                executor.submit(send_ping)
                log_it("i", "Started ping thread for WebSocket server")
            log_it("i", f"{Config.PLUGIN_NAME} started!")
            return 0
        except Exception as e:
            log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())

    def deinit():
        log_it("i", f"{Config.PLUGIN_NAME} stopped")
        return 0
except Exception as e:
    log_it("e", f"Fatal error during startup: {e}", exc=traceback.format_exc())