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

    executor = ThreadPoolExecutor(max_workers=2)

    def http_server():
        try:
            handler = CFSimpleHTTPRequestHandler(methods=["GET"], handler=request_handler)
            CFSimpleHTTPServer().register_uri_handler(uri=f"/{Config.PLUGIN_URL}", handler=handler)
            log_it("i", "HTTP server started")
        except Exception as e:
            log_it("e", "An error occurred", exc=e)

    def init():
        try:
            hidden_keys = ["TOKEN", "PASSWORD", "CHAT_ID", "USER", "RECIPIENTS"]
            log_it("i", f"========= Configuration for {Config.PLUGIN_NAME} =========")
            for key, value in vars(Config).items():
                if key.startswith("__"):
                    continue
                if any(hidden in key for hidden in hidden_keys):
                    log_it("i", f"{key}: ***")
                else:
                    log_it("i", f"{key}: {value}")
            log_it("i", f"==========================================================")
            if is_locked():
                log_it("i", "Cache lock found, releasing it...")
                release_lock()
            executor.submit(http_server)
            log_it("i", "HTTP server started!")
            executor.submit(setup_schedules)
            log_it("i", "Scheduled tasks started!")
            log_it("i", f"{Config.PLUGIN_NAME} started!")
            return 0
        except Exception as e:
            log_it("e", "An error occurred", exc=e)

    def deinit():
        log_it("i", f"{Config.PLUGIN_NAME} stopped")
        return 0
except Exception as e:
    log_it("e", "Fatal error during startup", exc=e)