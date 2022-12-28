from serial import Serial
from pyubx2 import UBXReader, UBXMessage
from pynmeagps import NMEAMessage
import logging as log
import atexit
import os
import uuid

try:
    import common.mqtt as mqtt
    import common.logconf as logconf
except ImportError:
    import mqtt
    import logconf


def onExit(mqClient):
    log.info("Exit application")
    if mqClient is not None:
        mqClient.disconnect()


def runSerialPublish(mqClient, ubr: UBXReader, publishTopicUbx, publishTopicNmea):
    while True:
        (rawData, parsedData) = ubr.read()
        log.debug(parsedData)
        if type(parsedData) == UBXMessage:
            mqClient.publish(publishTopicUbx, rawData)
        if type(parsedData) == NMEAMessage:
            mqClient.publish(publishTopicNmea, rawData)


def main():
    logLevel = str(os.getenv("UB_LOG_LEVEL"))
    serialDevice = str(os.getenv("UB_SERIAL_DEVICE"))
    serialBaud = int(os.getenv("UB_SERIAL_BAUD"))
    broker = str(os.getenv("UB_MQTT_HOST"))
    port = int(os.getenv("UB_MQTT_PORT"))
    clientName = str(os.getenv("UB_MQTT_CLIENT_NAME"))
    publishTopicUbx = str(os.getenv("UB_MQTT_UBX_PUBLISH_TOPIC"))
    publishTopicNmea = str(os.getenv("UB_MQTT_NMEA_PUBLISH_TOPIC"))

    logconf.setup_logging(logLevel)

    if clientName == "":
        log.info("mqtt client name is empty, assign uuid")
        clientName = str(uuid.uuid1())

    mqClient = mqtt.launch(clientName, broker, port, [], None)
    atexit.register(onExit, mqClient)

    stream = Serial(serialDevice, serialBaud, timeout=3)
    ubr = UBXReader(stream)
    log.info('start publishing UBX messages from "{device}" to {topic}'.format(device=serialDevice, topic=publishTopicUbx))
    log.info('start publishing NMEA messages from "{device}" to {topic}'.format(device=serialDevice, topic=publishTopicNmea))
    runSerialPublish(mqClient, ubr, publishTopicUbx, publishTopicNmea)


if __name__ == "__main__":
    main()
