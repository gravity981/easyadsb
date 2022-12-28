import logging as log
import atexit
import os
import uuid
import time
import json

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


def runPeriodicPublish(mqClient, publishTopic):
    intervalSeconds = 1
    while True:
        log.info("collect and publish sysinfo")
        time.sleep(intervalSeconds)


def main():
    logLevel = str(os.getenv("SY_LOG_LEVEL"))
    broker = str(os.getenv("SY_MQTT_HOST"))
    port = int(os.getenv("SY_MQTT_PORT"))
    clientName = str(os.getenv("SY_MQTT_CLIENT_NAME"))
    publishTopic = str(os.getenv("SY_MQTT_PUBLISH_TOPIC"))

    logconf.setupLogging(logLevel)

    if clientName == "":
        log.info("mqtt client name is empty, assign uuid")
        clientName = str(uuid.uuid1())

    mqClient = mqtt.launch(clientName, broker, port, [], None)
    atexit.register(onExit, mqClient)

    runPeriodicPublish(mqClient, publishTopic)


if __name__ == "__main__":
    main()
