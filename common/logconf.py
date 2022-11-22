import logging


def setup_logging(level: str):
    fmt = "[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d] - %(message)s"
    if level == "DEBUG":
        log_level = logging.DEBUG
    elif level == "INFO":
        log_level = logging.INFO
    elif level == "WARNING":
        log_level = logging.WARNING
    else:
        log_level = logging.WARNING
    logging.basicConfig(level=log_level, format=fmt)
