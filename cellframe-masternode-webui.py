from config import Config
from handlers import request_handler
from logger import log_it
from pycfhelpers.node.http.simple import CFSimpleHTTPServer, CFSimpleHTTPRequestHandler
from run_scheduler import setup_schedules
import threading

def http_server():
    try:
        handler = CFSimpleHTTPRequestHandler(methods=["GET"], handler=request_handler)
        CFSimpleHTTPServer().register_uri_handler(uri=f"/{Config.PLUGIN_URL}", handler=handler)
        log_it("i", "HTTP server started")
    except Exception as e:
        log_it("e", "An error occurred", exc=e)

def init():
    try:
        t_http_server = threading.Thread(target=http_server)
        t_scheduled_tasks = threading.Thread(target=setup_schedules)
        t_http_server.start()
        log_it("i", "HTTP server started!")
        t_scheduled_tasks.start()
        log_it("i", "Scheduled tasks started!")
        log_it("i", f"{Config.PLUGIN_NAME} started!")
        return 0
    except Exception as e:
        log_it("e", "An error occurred", exc=e)

def deinit():
    log_it("i", f"{Config.PLUGIN_NAME} stopped")
    return 0
