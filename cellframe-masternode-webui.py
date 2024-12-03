from pycfhelpers.node.http.simple import CFSimpleHTTPServer, CFSimpleHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor
from logger import log_it
from handlers import requestHandler
from config import Config
import threading

def http_server():
    try:
        handler = CFSimpleHTTPRequestHandler(methods=["GET"], handler=requestHandler)
        CFSimpleHTTPServer().register_uri_handler(uri=f"/{Config.PLUGIN_URI}", handler=handler)
        log_it("i", "HTTP server started")
    except Exception as e:
        log_it("e", f"Error: {e}")
    return 0

def init():
    try:
        t = threading.Thread(target=on_init)
        t.start()
    except Exception as e:
        log_it("e", f"Error: {e}")
    return 0

def on_init():
    try:
        with ThreadPoolExecutor() as executor:
            log_it("i", "Submitting HTTP server to ThreadPool")
            executor.submit(http_server)    
    except Exception as e:
        log_it("e", f"Error: {e}")

def deinit():
    return 0
