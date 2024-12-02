import logging
import os
import threading
import inspect
from config import Config

logLock = threading.Lock()

log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "webui.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(funcName)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def logger(level, msg):
    with logLock:
        caller_frame = inspect.currentframe().f_back
        func_name = caller_frame.f_code.co_name
        
        levels = {
            "notice": logging.info,
            "error": logging.error,
        }
        
        log_func = levels.get(level.lower(), None)
        
        if log_func:
            log_func(f"[{func_name}] {msg}")
        else:
            logging.warning(f"[{func_name}] Unsupported log level: {level}. Message: {msg}")

def logDebug(func):
    if Config.DEBUG:
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            logging.info(f"Calling {func_name} with args: {args}, kwargs: {kwargs}")
            result = func(*args, **kwargs)
            logging.info(f"{func_name} returned: {result}")
            return result
        return wrapper
    else:
        return func
