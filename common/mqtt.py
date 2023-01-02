import paho.mqtt.client as mq
import logging as log
import time
import threading
from concurrent.futures import ThreadPoolExecutor, Future
import json
import uuid


def launch(client_name, host, port, topics: list = [], msgCallback=None) -> mq.Client:
    """
    launches mqtt client, aborts if connection is not successful
    """
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            log.info("mqtt connected")
            for t in topics:
                client.subscribe(t)
                log.info("subscribed to topic {}".format(t))
        else:
            log.warning("could not connect to mqtt server. code: %s", str(rc))

    def on_disconnect(client, userdata, rc):
        log.info(
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
                log.error("could not connect to mqtt broker, {}".format(str(ex)))
                failureReported = True
            time.sleep(5)
    log.info("mqtt launched")


class RequestMessage(dict):

    def __init__(self, command: str, data: dict):
        self["command"] = command
        self["data"] = data


class ResponseMessage(dict):

    def __init__(self, success: bool, data):
        self["success"] = success
        self["data"] = data


class MqttMessenger:
    """
    dispatch incoming mqtt messages to correct receiver
    supports dispatching of requests and responses
    works only with json string message payloads
    """
    REQUEST = 1
    RESPONSE = 2
    NOTIFICATION = 3

    def __init__(self, mqClient, subscriptions):
        self._mqClient = mqClient
        self._executor = ThreadPoolExecutor(max_workers=3)
        self._requestFutures = dict()
        self._responseFutures = dict()
        self._subscriptions = dict()
        for topic, meta in subscriptions.items():
            if meta["type"] == MqttMessenger.REQUEST:
                topic += "/request"
            elif meta["type"] == MqttMessenger.RESPONSE:
                topic += "/response"
            self._mqClient.subscribe(topic)
            self._subscriptions[topic] = meta
            log.info("subscribed for topic {}".format(topic))
        self._mqClient.on_message = self._onMessage
        self._mqClient.on_connect = self._onConnect

    def sendNotification(self, topic, msg):
        self._mqClient.publish(topic, json.dumps(msg))

    def sendRequestAndWait(self, topic, msg: RequestMessage, timeout=3):
        if not topic.endswith("/request"):
            topic += "/request"
        requestId = str(uuid.uuid1())
        future = Future()
        self._responseFutures[requestId] = future
        msg["requestId"] = requestId
        self._mqClient.publish(topic, json.dumps(msg))
        return future.result(timeout)

    def _onConnect(self, client, userdata, flags, rc):
        if rc == 0:
            log.info("mqtt connected")
            for topic in self._subscriptions.keys():
                client.subscribe(topic)
                log.info("subscribed to topic {}".format(topic))
        else:
            log.warning("could not connect to mqtt server. code: %s", str(rc))

    def _onMessage(self, client, userdata, msg):
        try:
            msgStr = msg.payload.decode("UTF-8").strip()
            msgData = json.loads(msgStr)
            if msg.topic in self._subscriptions.keys():
                sub = self._subscriptions[msg.topic]
                if sub["type"] == MqttMessenger.REQUEST:
                    requestId = msgData.pop("requestId")
                    responseTopic = self._getResponseTopic(msg.topic)
                    request = RequestMessage(msgData["command"], msgData["data"])
                    future = self._executor.submit(sub["func"], request)
                    self._requestFutures[future] = (responseTopic, requestId)
                    future.add_done_callback(self._requestExecuted)
                elif sub["type"] == MqttMessenger.RESPONSE:
                    future = self._responseFutures.pop(msgData["requestId"])
                    response = ResponseMessage(msgData["success"], msgData["data"])
                    future.set_result(response)
                    future.done()
                elif sub["type"] == MqttMessenger.NOTIFICATION:
                    self._executor.submit(sub["func"], msgData)
                else:
                    log.error("unknown subscription type")
            else:
                log.error("no subscription for topic {}".format(msg.topic))
        except ValueError as ex:
            log.error("ValueError occured, {}".format(str(ex)))
        except KeyError:
            log.error("KeyError occured")

    def _requestExecuted(self, future):
        topic, requestId = self._requestFutures.pop(future)
        ex = future.exception()
        data = None
        if future.cancelled():
            success = False
            log.warning("request execution cancelled")
        elif ex is not None:
            success = False
            log.warning("request execution failed with {}, {}".format(type(ex), str(ex)))
        else:
            success = True
            data = future.result()
        response = ResponseMessage(success, data)
        response["requestId"] = requestId
        self._mqClient.publish(topic, json.dumps(response))

    def _getResponseTopic(self, requestTopic):
        if "request" in requestTopic:
            return requestTopic.rstrip("request") + "response"
        else:
            raise ValueError("not a request topic")
