import logging, os, inspect
from config import Config
from logging.handlers import RotatingFileHandler

log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "webui.log")

handler = RotatingFileHandler(
    log_file,
    maxBytes=5 * 1024 * 1024,
    backupCount=5
)

formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] [%(funcName)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

handler.setFormatter(formatter)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

def log_it(level, msg, exc=None):
    caller_frame = inspect.currentframe().f_back
    func_name = caller_frame.f_code.co_name
    filename = caller_frame.f_code.co_filename

    if level.lower() == "d" and not Config.DEBUG:
        return

    levels = {
        "i": logging.info,
        "e": logging.error,
        "d": logging.info,
    }

    log_func = levels.get(level.lower(), None)

    if log_func:
        if exc:
            log_func(f"[{func_name}] [{filename}] {msg} - Exception: {exc}")
        elif level.lower() == "d":
            log_func(f"[DEBUG] [{func_name}] {msg}")
        else:
            log_func(f"[{func_name}] {msg}")
    else:
        logging.error(f"[{func_name}] Unsupported log level: {level}. Message: {msg}")
