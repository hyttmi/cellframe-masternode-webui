import logging
import os
import threading
import inspect
from config import Config

logLock = threading.Lock()

def getScriptDir():
    return os.path.dirname(os.path.abspath(__file__))

log_file = os.path.join(getScriptDir(), "webui.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(funcName)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def logNotice(msg):
    with logLock:
        func_name = inspect.stack()[1].function
        logging.info(f"[{func_name}] {msg}")

def logError(msg):
    with logLock:
        func_name = inspect.stack()[1].function
        logging.error(f"[{func_name}] {msg}")

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
