import paho.mqtt.client as mq
import logging

logger = logging.getLogger("logger")


def launch(client_name, host, port) -> mq.Client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logger.info("mqtt connected")
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
    client.connect(host, port, keepalive=60)
    client.loop_start()
    return client
