import paho.mqtt.client as mq
import logging
import time
import threading

logger = logging.getLogger("logger")


def launch(client_name, host, port, topics: list, msgCallback) -> mq.Client:
    """
    launches mqtt client, aborts if connection is not successful
    """
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logger.info("mqtt connected")
            for t in topics:
                client.subscribe(t)
                logger.info("subscribed to topic {}".format(t))
        else:
            logger.warning("could not connect to mqtt server. code: %s", str(rc))

    def on_disconnect(client, userdata, rc):
        logger.info(
            "disconnected from mqtt server, code: %s, userdata: %s",
            str(rc),
            str(userdata),
        )

    client = mq.Client(client_name)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = msgCallback
    client.connect(host, port, keepalive=60)
    client.loop_start()
    return client


def launchStart(client_name, host, port, topics: list, msgCallback):
    """
    repeatedly tries to launch mqtt client in background
    """
    mqttLauncher = threading.Thread(target=_launchInBackground, args=[client_name, host, port, topics, msgCallback], name="mqttLauncher")
    mqttLauncher.start()


def _launchInBackground(client_name, host, port, topics: list, msgCallback):
    failureReported = False
    while True:
        try:
            launch(client_name, host, port, topics, msgCallback)
            break
        except ConnectionRefusedError as ex:
            if not failureReported:
                logger.error("could not connect to mqtt broker, {}".format(str(ex)))
                failureReported = True
            time.sleep(5)
    logger.info("mqtt launched")
