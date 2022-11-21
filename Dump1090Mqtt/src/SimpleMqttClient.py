import logging
import paho.mqtt.client as mqtt
import socket
import time


class SimpleMqttClient:
    def __init__(self, host, port, keepalive, client_name, logger_name):
        self.logger = logging.getLogger(logger_name)
        self.client = mqtt.Client(client_name)
        self.on_connection_state_changed = None
        self.host = host
        self.port = port
        self.keepalive = keepalive
        self.is_connected = False

    def __on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.is_connected = True
            self.logger.info("connected to mqtt server")
            if self.on_connection_state_changed is not None:
                self.on_connection_state_changed(self.is_connected)
        else:
            self.logger.error("could not connect to mqtt server. code: %s", str(rc))

    def __on_disconnect(self, client, userdata, rc):
        self.logger.info("disconnected from mqtt server, code: %s, userdata: %s", str(rc), str(userdata))

    def connect(self):
        self.client.on_connect = self.__on_connect
        self.client.on_disconnect = self.__on_disconnect
        success = False
        while not success:
            try:
                self.logger.info("connect to mqtt server ({host}:{port}) ...".format(host=self.host, port=self.port))
                self.client.connect(self.host, port=self.port, keepalive=self.keepalive)
                success = True
            except TimeoutError:
                self.logger.error("mqtt connection failed. mqtt server offline? incorrect configuration?")
            except ConnectionRefusedError:
                self.logger.error("connection refused")
                break
            except socket.gaierror:
                self.logger.error("host unreachable. offline?")
                time.sleep(5)
        if success:
            self.logger.info("connection successful")
            self.client.loop_start()
        else:
            self.logger.error("connection failed")
        return success

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

    def publish(self, topic, message):
        if self.client.is_connected():
            self.client.publish(topic, payload=message)
            return True
        else:
            self.logger.warning("cannot publish message, client is not connected")
        return False
