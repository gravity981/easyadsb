import logging
import atexit
import os
import socket
import uuid
import time

try:
    import common.mqtt as mqtt
    import common.logconf as logconf
except ImportError:
    import mqtt
    import logconf


def on_exit():
    global run
    if logger is not None:
        logger.info("exit application")
    if client is not None:
        client.disconnect()
    run = False


# works for protocols which have pakets that end on \n
def socket_readline(skt):
    buf_size = 4096
    line = skt.recv(buf_size, socket.MSG_PEEK)
    if len(line) == 0:
        raise Exception("connection lost")
    elif len(line) < 5:
        logger.warning('very short message, "{}"'.format(line))
    eol = line.find(b"\n")
    if eol >= 0:
        size = eol + 1
    else:
        logger.warning("unable to find end of message")
        size = len(line)
    return skt.recv(size)


def run_tcp_publish(sock):
    global tcp_connected
    while run:
        try:
            line = socket_readline(sock)
            logger.debug(line)
            client.publish(publish_topic, line)
        except Exception as ex:
            logger.error("socket readline error, {}".format(str(ex)))
            tcp_connected = False
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            logger.info('try reconnecting to "{}:{}"'.format(tcp_host, tcp_port))
            while not tcp_connected:
                try:
                    sock.connect((tcp_host, tcp_port))
                    tcp_connected = True
                    logger.info("reconnected")
                except socket.error:
                    time.sleep(5)


if __name__ == "__main__":
    logger = None
    client = None
    run = True
    tcp_connected = False

    logger_name = "logger"
    log_level = str(os.getenv("DU_LOG_LEVEL"))
    tcp_host = str(os.getenv("DU_TCP_HOST"))
    tcp_port = int(os.getenv("DU_TCP_PORT"))
    broker = str(os.getenv("DU_MQTT_HOST"))
    port = int(os.getenv("DU_MQTT_PORT"))
    client_name = str(os.getenv("DU_MQTT_CLIENT_NAME"))
    publish_topic = str(os.getenv("DU_MQTT_PUBLISH_TOPIC"))

    logconf.setup_logging(log_level)
    logger = logging.getLogger(logger_name)
    atexit.register(on_exit)

    if client_name == "":
        logger.info("client_name is empty, assign uuid")
        client_name = str(uuid.uuid1())

    client = mqtt.launch(client_name, broker, port, [], None)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    logger.debug('connect to "{host}:{port}"'.format(host=tcp_host, port=tcp_port))
    sock.connect((tcp_host, tcp_port))
    tcp_connected = True
    logger.info('start publishing messages from "{host}:{port}" to {topic}'.format(host=tcp_host, port=tcp_port, topic=publish_topic))
    run_tcp_publish(sock)

    exit()
