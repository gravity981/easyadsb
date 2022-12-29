import logging
import hashlib
import binascii


def setupLogging(level: str):
    fmt = "[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d] - %(message)s"
    if level == "DEBUG":
        logLevel = logging.DEBUG
    elif level == "INFO":
        logLevel = logging.INFO
    elif level == "WARNING":
        logLevel = logging.WARNING
    else:
        logLevel = logging.WARNING
    logging.basicConfig(level=logLevel, format=fmt)


def wpaPsk(ssid, password):
    dk = hashlib.pbkdf2_hmac('sha1', str.encode(password), str.encode(ssid), 4096, 32)
    return (binascii.hexlify(dk))
