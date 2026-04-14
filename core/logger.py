import logging
import sys

def setup_logger(name: str = None):
    logger = logging.getLogger(name or "app")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        fmt = "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
        handler.setFormatter(logging.Formatter(fmt, "%Y-%m-%d %H:%M:%S"))
        logger.addHandler(handler)
        logger.setLevel('INFO')
        logger.propagate = False
    return logger

# convenience
logger = setup_logger("app_utils")