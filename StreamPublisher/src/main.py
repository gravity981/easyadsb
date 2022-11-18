from serial import Serial
import logging
import atexit
import os
import SimpleMqttClient
import socket
import uuid

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

def run_serial_publish(mqtt, stream):
    while(run):
        line = stream.readline()
        logger.debug(line)
        client.publish(publish_topic, line) 

def run_tcp_publish(mqtt, sock):
    while(run):
        line = socket_readline(sock)
        logger.debug(line)
        client.publish(publish_topic, line)  

if __name__ == '__main__':
    logger = None
    client = None
    run = True

    logger_name="logger"
    log_level = str(os.getenv('SR_LOG_LEVEL', default='INFO'))
    input_mode = str(os.getenv('SR_INPUT_MODE'))

    serial_device = str(os.getenv('SR_SERIAL_DEVICE', default='/dev/ttyAMA0'))
    serial_baud = int(os.getenv('SR_SERIAL_BAUD', default=9600))
    
    tcp_host = str(os.getenv('SR_TCP_HOST', default='localhost'))
    tcp_port = int(os.getenv('SR_TCP_PORT', default=30003))
    
    broker = str(os.getenv('SR_MQTT_HOST', default='localhost'))
    port = int(os.getenv('SR_MQTT_PORT', default=1883))
    client_name = str(os.getenv('SR_MQTT_CLIENT_NAME'))
    publish_topic = str(os.getenv('SR_MQTT_PUBLISH_TOPIC', default='/gps/nmea'))

    setup_logging(log_level)
    logger = logging.getLogger(logger_name)
    atexit.register(on_exit)

    if client_name == "":
        logger.info("client_name is empty, assign uuid")
        client_name = str(uuid.uuid1())

    client = SimpleMqttClient.SimpleMqttClient(broker, port, 60, client_name, logger_name)
    if not client.connect():
        exit()

    if input_mode == "SERIAL":
        stream = Serial(serial_device, serial_baud, timeout=3)
        logger.info("start publishing serial stream from \"{device}\"".format(device=serial_device))
        run_serial_publish(client, stream)
    elif input_mode == "TCP":
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logger.debug("connect to \"{host}:{port}\"".format(host=tcp_host, port=tcp_port))
        sock.connect((tcp_host,tcp_port))
        logger.info("start publishing tcp stream from \"{host}:{port}\"".format(host=tcp_host, port=tcp_port))
        run_tcp_publish(client, sock)
    else:
        logger.error("unsupported input mode \"{mode}\"".format(mode=input_mode))
    exit()
    

