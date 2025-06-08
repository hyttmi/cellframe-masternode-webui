from logger import log_it
import sys
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
    from thread_launcher import start_thread
    from notifications import notify_all

    def http_server():
        try:
            handler = CFSimpleHTTPRequestHandler(methods=["GET", "POST"], handler=request_handler)
            CFSimpleHTTPServer().register_uri_handler(uri=f"/{Config.PLUGIN_URL}", handler=handler)
            log_it("i", "HTTP server started")
        except Exception as e:
            log_it("e", f"An error occurred in HTTP server: {e}", exc=traceback.format_exc())

    def init():
        try:
            if is_locked():
                log_it("i", "Cache lock found, releasing it...")
                release_lock()

            start_thread(http_server)
            log_it("i", "HTTP server started on thread")

            start_thread(setup_schedules)
            log_it("i", "Scheduled tasks started on thread")

            start_thread(start_ws_server, Config.WEBSOCKET_SERVER_PORT)

            log_it("i", f"{Config.PLUGIN_NAME} on {Config.NODE_ALIAS} started!")
            notify_all(f"{Config.PLUGIN_NAME} on {Config.NODE_ALIAS} started!") # This doesn't block the main thread really
            return 0
        except Exception as e:
            log_it("e", f"An error occurred during init: {e}", exc=traceback.format_exc())

    def deinit():
        log_it("i", f"{Config.PLUGIN_NAME} stopped")
        return 0

except Exception as e:
    log_it("e", f"Fatal error during startup: {e}", exc=traceback.format_exc())
