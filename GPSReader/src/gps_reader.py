from serial import Serial
from pynmeagps import NMEAReader
import logging
import atexit
import os
import SimpleMqttClient
import socket

def setup_logging(level: str):
    fmt = '[%(asctime)s][%(levelname)-8s][%(filename)s:%(lineno)d] - %(message)s'
    if level == 'DEBUG':
        log_level = logging.DEBUG
    elif level == 'INFO':
        log_level = logging.INFO
    elif level == 'WARNING':
        log_level = logging.WARNING
    else:
        log_level = logging.WARNING
    logging.basicConfig(level=log_level, format=fmt)

def on_exit():
    global run
    if logger is not None:
        logger.info('Exit application')
    if client is not None:
        client.disconnect()
    run = False


def socket_readline(skt):
    buf_size = 4096
    line = skt.recv(buf_size, socket.MSG_PEEK)
    eol = line.find(b'\n')
    if eol >= 0:
        size = eol + 1
    else:
        logger.warning('Unable to find end of message')
        size = len(line)
    return skt.recv(size)


if __name__ == '__main__':
    logger = None
    client = None
    run = True
    log_level = str(os.getenv('GR_LOG_LEVEL', default='INFO'))
    serial_device = str(os.getenv('GR_SERIAL_DEVICE', default='/dev/ttyAMA0'))
    broker = str(os.getenv('GR_MQTT_HOST', default='localhost'))
    port = int(os.getenv('GR_MQTT_PORT', default=1883))
    client_name = str(os.getenv('GR_MQTT_CLIENT_NAME', default='gps_readerr'))
    publish_topic = str(os.getenv('GR_MQTT_PUBLISH_TOPIC', default='/gps/nmea'))

    setup_logging(log_level)
    logger = logging.getLogger(client_name)
    atexit.register(on_exit)

    client = SimpleMqttClient.SimpleMqttClient(broker, port, 60, client_name, client_name)
    if not client.connect():
        exit()

    # serial stream
    stream = Serial(serial_device, 9600, timeout=3)

    # tcp stream
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # now connect to the web server on port 80 - the normal http port
    s.connect(("localhost",30003))

    with stream:
        while(run):
            # line = stream.readline()
            line = socket_readline(s)
            logger.debug(line)
            client.publish(publish_topic, line)     
