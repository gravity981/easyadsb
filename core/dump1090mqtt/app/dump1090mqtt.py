import logging as log
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


def onExit(mqClient):
    log.info("exit application")
    if mqClient is not None:
        mqClient.disconnect()


# works for protocols which have frames that end on \n
def socketReadline(skt):
    bufSize = 4096
    line = skt.recv(bufSize, socket.MSG_PEEK)
    if len(line) == 0:
        raise Exception("connection lost")
    elif len(line) < 5:
        log.warning('very short message, "{}"'.format(line))
    eol = line.find(b"\n")
    if eol >= 0:
        size = eol + 1
    else:
        log.warning("unable to find end of message")
        size = len(line)
    return skt.recv(size)


def runTcpPublish(sock, mqClient, publishTopic, tcpHost, tcpPort, tcpConnected):
    while True:
        try:
            line = socketReadline(sock)
            log.debug(line)
            mqClient.publish(publishTopic, line)
        except Exception as ex:
            log.error("socket readline error, {}".format(str(ex)))
            tcpConnected = False
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            log.info('try reconnecting to "{}:{}"'.format(tcpHost, tcpPort))
            while not tcpConnected:
                try:
                    sock.connect((tcpHost, tcpPort))
                    tcpConnected = True
                    log.info("reconnected")
                except socket.error:
                    time.sleep(5)


def main():
    logLevel = str(os.getenv("DU_LOG_LEVEL"))
    tcpHost = str(os.getenv("DU_TCP_HOST"))
    tcpPort = int(os.getenv("DU_TCP_PORT"))
    broker = str(os.getenv("DU_MQTT_HOST"))
    port = int(os.getenv("DU_MQTT_PORT"))
    clientName = str(os.getenv("DU_MQTT_CLIENT_NAME"))
    publishTopic = str(os.getenv("DU_MQTT_PUBLISH_TOPIC"))

    logconf.setupLogging(logLevel)

    if clientName == "":
        log.info("mqtt client name is empty, assign uuid")
        clientName = str(uuid.uuid1())

    mqClient = mqtt.launch(clientName, broker, port, [], None)
    atexit.register(onExit, mqClient)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    log.debug('connect to "{host}:{port}"'.format(host=tcpHost, port=tcpPort))
    sock.connect((tcpHost, tcpPort))
    log.info('start publishing messages from "{host}:{port}" to {topic}'.format(host=tcpHost, port=tcpPort, topic=publishTopic))
    runTcpPublish(sock, mqClient, publishTopic, tcpHost, tcpPort, True)


if __name__ == "__main__":
    main()
