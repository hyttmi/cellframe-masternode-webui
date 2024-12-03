import logging
import os
import threading
import inspect
from config import Config
from sysutils import get_current_script_directory

logLock = threading.Lock()

log_file = os.path.join(get_current_script_directory(), "webui.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(funcName)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def log_it(level, msg):
    with logLock:
        caller_frame = inspect.currentframe().f_back
        func_name = caller_frame.f_code.co_name
        
        levels = {
            "i": logging.info,
            "e": logging.error,
        }
        
        log_func = levels.get(level.lower(), None)
        
        if log_func:
            log_func(f"[{func_name}] {msg}")
        else:
            logging.error(f"[{func_name}] Unsupported log level: {level}. Message: {msg}")

def log_debug(func):
    if Config.DEBUG:
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            log_it("i", f"Calling {func_name} with args: {args}, kwargs: {kwargs}")
            result = func(*args, **kwargs)
            log_it("i", f"{func_name} returned: {result}")
            return result
        return wrapper
    else:
        return func
