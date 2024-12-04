try:
    from pycfhelpers.node.http.simple import CFSimpleHTTPServer, CFSimpleHTTPRequestHandler
    from concurrent.futures import ThreadPoolExecutor
    from logger import log_it
    from handlers import request_handler
    from config import Config
    from cacher import cache_blocks_data, cache_rewards_data
    from scheduler import run_scheduler
    import threading
except ImportError as e:
    log_it("e", f"ImportError: {e}")

def http_server():
    try:
        handler = CFSimpleHTTPRequestHandler(methods=["GET"], handler=request_handler)
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
            log_it("i", "Submitting blocks caching to ThreadPool")
            executor.submit(run_scheduler, cache_blocks_data, Config.CACHE_BLOCKS_INTERVAL)
            log_it("i", "Submitting rewards caching to ThreadPool")
            executor.submit(run_scheduler, cache_rewards_data, Config.CACHE_REWARDS_INTERVAL)
    except Exception as e:
        log_it("e", f"Error: {e}")

def deinit():
    return 0
