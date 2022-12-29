
from common.mqtt import MqttMessenger, RequestMessage
import json
from concurrent.futures import Future, ThreadPoolExecutor


class FakeMqClient:

    def __init__(self):
        self._future = Future()
        self.on_message = None

    def publish(self, topic, msg):
        self._future.set_result((topic, msg))
        self._future.done()

    def subscribe(self, topic):
        pass

    def waitForPublish(self, timeout=None):
        return self._future.result(timeout)


class FakeMqMessage:

    def __init__(self, topic, data):
        self.topic = topic
        self.payload = json.dumps(data).encode("utf-8")


def test_messengerProcessRequestMessage():

    def doWork(msg):
        assert msg["command"] == "doSomething"
        assert msg["data"]["param1"] is True
        return {"hello": "world"}

    subscriptions = {
        "topic1": {
            "type": MqttMessenger.REQUEST,
            "func": doWork
        }
    }
    mqClient = FakeMqClient()
    messenger = MqttMessenger(mqClient, subscriptions)
    data = {
        "requestId": 1234,
        "command": "doSomething",
        "data": {"param1": True}
    }
    msg = FakeMqMessage("topic1/request", data)
    mqClient.on_message(None, None, msg)
    topic, msg = mqClient.waitForPublish(1)
    msg = json.loads(msg)
    assert "success" in msg
    assert "requestId" in msg
    assert "data" in msg
    assert "topic1/response" == topic
    assert msg["success"] is True
    assert msg["requestId"] == 1234
    assert msg["data"]["hello"] == "world"


def test_messengerProcessResponseMessage():
    subscriptions = {
        "topic1": {
            "type": MqttMessenger.RESPONSE,
        }
    }
    mqClient = FakeMqClient()
    messenger = MqttMessenger(mqClient, subscriptions)
    msg = RequestMessage("doSomething", {"hello": "world"})
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(messenger.sendRequestAndWait, "topic1/request", msg, 1)
        topic, msg = mqClient.waitForPublish(1)
        msg = json.loads(msg)
        assert topic == "topic1/request"
        assert msg["requestId"] is not None
        assert msg["command"] == "doSomething"
        assert msg["data"]["hello"] == "world"
        data = {
            "requestId": msg["requestId"],
            "success": True,
            "data": None
        }
        msg = FakeMqMessage("topic1/response", data)
        mqClient.on_message(None, None, msg)
        response = future.result(1)
        assert response["success"] is True
        assert response["data"] is None
