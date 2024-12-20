from concurrent.futures import ThreadPoolExecutor
from config import Config
from handlers import request_handler
from logger import log_it
from pycfhelpers.node.http.simple import CFSimpleHTTPServer, CFSimpleHTTPRequestHandler
from run_scheduler import setup_schedules
import threading, inspect

def http_server():
    try:
        handler = CFSimpleHTTPRequestHandler(methods=["GET"], handler=request_handler)
        CFSimpleHTTPServer().register_uri_handler(uri=f"/{Config.PLUGIN_URL}", handler=handler)
        log_it("i", "HTTP server started")
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")

def init():
    try:
        t = threading.Thread(target=on_init)
        t.start()
        log_it("i", f"{Config.PLUGIN_NAME} started")
        return 0
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")

def on_init():
    try:
        with ThreadPoolExecutor() as executor:
            log_it("i", "Submitting HTTP server to ThreadPool")
            executor.submit(http_server)
            log_it("i", "Submitting scheduled tasks to ThreadPool")
            executor.submit(setup_schedules)
    except Exception as e:
        log_it("e", f"Error: {e}")

def deinit():
    log_it("i", f"{Config.PLUGIN_NAME} stopped")
    return 0
