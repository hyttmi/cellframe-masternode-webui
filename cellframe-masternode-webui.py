from logger import log_it
import sys
import threading
import traceback

# Redirect stderr to logger
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
    from websocket_server import start_ws_server
    from utils import is_port_available

    def http_server():
        try:
            handler = CFSimpleHTTPRequestHandler(methods=["GET", "POST"], handler=request_handler)
            CFSimpleHTTPServer().register_uri_handler(uri=f"/{Config.PLUGIN_URL}", handler=handler)
            log_it("i", "HTTP server started")
        except Exception as e:
            log_it("e", f"An error occurred in HTTP server: {e}", exc=traceback.format_exc())

    def init():
        try:
            current_config = Config.get_current_config(hide_sensitive_data=True)
            for key, value in current_config.items():
                log_it("d", f"{key}: {value}")

            if is_locked():
                log_it("i", "Cache lock found, releasing it...")
                release_lock()

            threading.Thread(target=http_server, daemon=True).start()
            log_it("i", "HTTP server started on thread")

            threading.Thread(target=setup_schedules, daemon=True).start()
            log_it("i", "Scheduled tasks started on thread")

            if Config.WEBSOCKET_SERVER_PORT < 1024 or Config.WEBSOCKET_SERVER_PORT > 65535:
                log_it("e", f"Invalid WebSocket server port: {Config.WEBSOCKET_SERVER_PORT}. Must be between 1024 and 65535.")
            elif not is_port_available(Config.WEBSOCKET_SERVER_PORT):
                log_it("e", f"WebSocket server port {Config.WEBSOCKET_SERVER_PORT} is not available.")
            else:
                threading.Thread(target=start_ws_server, args=(Config.WEBSOCKET_SERVER_PORT,), daemon=True).start()
                log_it("i", f"WebSocket server started on thread")

            log_it("i", f"{Config.PLUGIN_NAME} on {Config.NODE_ALIAS} started!")
            return 0
        except Exception as e:
            log_it("e", f"An error occurred during init: {e}", exc=traceback.format_exc())

    def deinit():
        log_it("i", f"{Config.PLUGIN_NAME} stopped")
        return 0

except Exception as e:
    log_it("e", f"Fatal error during startup: {e}", exc=traceback.format_exc())
