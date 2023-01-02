import logging as log
import uuid
import atexit
import os
from pyubx2 import UBXReader
from pynmeagps import NMEAReader
from sbs import SBSReader
from positioning import NavMonitor, PosInfo, NavMode
from traffic import TrafficMonitor, TrafficEntry
from gdl90 import (
    GDL90Port,
    GDL90EmitterCategory,
    GDL90MiscellaneousIndicatorTrack,
    GDL90MiscellaneousIndicatorAirborne,
    GDL90OwnshipMessage,
    GDL90OwnshipGeoAltitudeMessage,
    GDL90HeartBeatMessage,
    GDL90TrafficMessage
)
from datetime import datetime
import threading
import json

try:
    import common.mqtt as mqtt
    import common.util as util
except ImportError:
    import mqtt
    import util


def onExit():
    log.info("Exit application")


class MessageDispatcher:
    """
    used to parse incoming mqtt messages and dispatch them to the correct receiver
    """

    def __init__(self, navMonitor, trafficMonitor):
        self._navMonitor = navMonitor
        self._trafficMonitor = trafficMonitor

    def onNmeaMessage(self, msg):
        try:
            nmea = NMEAReader.parse(msg)
            log.debug(nmea)
            self._navMonitor.update(nmea)
        except Exception as ex:
            log.error('on nmea message error, {}, "{}"'.format(str(ex), msg))
            return

    def onUbxMessage(self, msg):
        try:
            ubx = UBXReader.parse(msg.strip())
            log.debug(ubx)
        except Exception as ex:
            log.error('on ubx message error, {}, "{}"'.format(str(ex), msg))
            return

    def onSbsMessage(self, msg):
        try:
            dec = msg.strip()
            sbs = SBSReader.parse(dec)
            log.debug(sbs)
            self._trafficMonitor.update(sbs)
        except UnicodeDecodeError:
            log.error('on sbs message decode error, "{}"'.format(msg))
            return
        except Exception as ex:
            log.error('on sbs message error, {}, "{}"'.format(str(ex), msg))
            return

    def onBmeMessage(self, msg):
        try:
            bme = json.loads(msg.strip())
            log.debug(bme)
            self._navMonitor.updateBme(bme)
        except Exception as ex:
            log.error('on bme message error, {}, "{}"'.format(str(ex), msg.payload))
            return

    def onTrafficRequest(self, msg):
        if "command" in msg.keys():
            if msg["command"] == "clearHistory":
                log.info("cleanup unseen traffic")
                self._trafficMonitor.cleanup()
            if msg["command"] == "setAutoCleanup":
                if msg["data"]["enabled"]:
                    self._trafficMonitor.startAutoCleanup()
                else:
                    self._trafficMonitor.stopAutoCleanup()


class GDL90Sender:
    """
    used to send various GDL90 messages to a `GDL90Port`.
    Manages periodic GDL90 Heartbeat.
    """

    def __init__(self, gdl90Port: GDL90Port, navMonitor):
        self._gdl90Port = gdl90Port
        self._heartbeatIntervalSeconds = 1
        self._navMonitor = navMonitor
        self._sendHeartbeatMsg()

    def notify(self, obj):
        if type(obj) == TrafficEntry:
            trafficMsg = MessageConverter.toGDL90TrafficMsg(obj)
            self._send(trafficMsg)
        elif type(obj) == PosInfo:
            ownshipMsg = MessageConverter.toGDL90OwnshipMsg(obj)
            ownshipAltMsg = MessageConverter.toGDL90OwnshipGeoAltMsg(obj)
            self._send(ownshipMsg)
            self._send(ownshipAltMsg)
        else:
            log.error("notified with unexpected object of type {}".format(type(obj)))

    def _send(self, msg):
        if self._gdl90Port.isActive:
            self._gdl90Port.putMessage(msg)

    def _sendHeartbeatMsg(self):
        try:
            self._timer = threading.Timer(self._heartbeatIntervalSeconds, self._sendHeartbeatMsg)
            self._timer.start()
            heartbeat = MessageConverter.toGDL90HeartbeatMsg(self._navMonitor.posInfo)
            self._send(heartbeat)
        except Exception as ex:
            log.error("error sending gdl90 heartbeat message, {}".format(str(ex)))


class MessageConverter:
    """
    static class to convert & create different types of messages.
    """

    def toGDL90OwnshipMsg(posInfo: PosInfo):
        return GDL90OwnshipMessage(
            latitude=posInfo.latitude if posInfo.latitude is not None else 0,
            longitude=posInfo.longitude if posInfo.longitude is not None else 0,
            altitude=posInfo.altitudeMeter * 3.28084 if posInfo.altitudeMeter is not None else 0,
            hVelocity=int(posInfo.groundSpeedKnots) if posInfo.groundSpeedKnots is not None else 0,
            vVelocity=0,
            trackHeading=posInfo.trueTrack if posInfo.trueTrack is not None else 0,
            navIntegrityCat=MessageConverter._getOwnshipNavScore(posInfo.navMode),
            navAccuracyCat=MessageConverter._getOwnshipNavScore(posInfo.navMode),
            emitterCat=GDL90EmitterCategory.light,
            trackIndicator=GDL90MiscellaneousIndicatorTrack.tt_true_track_angle,
            airborneIndicator=GDL90MiscellaneousIndicatorAirborne.airborne,
        )

    def toGDL90OwnshipGeoAltMsg(posInfo: PosInfo):
        return GDL90OwnshipGeoAltitudeMessage(
            altitude=posInfo.altitudeMeter * 3.28084 if posInfo.altitudeMeter is not None else 0, merit=50, isWarning=False
        )

    def toGDL90HeartbeatMsg(posInfo: PosInfo):
        seconds = MessageConverter._secondsSinceMidnightUTC(posInfo.utcTime)
        return GDL90HeartBeatMessage(
            isInitialized=seconds is not None,
            isLowBattery=False,
            time=seconds if seconds is not None else 0,
            posValid=posInfo.navMode != NavMode.NoFix,
        )

    def toGDL90TrafficMsg(trafficEntry: TrafficEntry):
        return GDL90TrafficMessage(
            latitude=trafficEntry.latitude if trafficEntry.latitude is not None else 0,
            longitude=trafficEntry.longitude if trafficEntry.longitude is not None else 0,
            altitude=trafficEntry.altitude if trafficEntry.altitude is not None else 0,
            hVelocity=trafficEntry.groundSpeed if trafficEntry.groundSpeed is not None else 0,
            vVelocity=trafficEntry.verticalSpeed if trafficEntry.verticalSpeed is not None else 0,
            trackHeading=trafficEntry.track if trafficEntry.track is not None else 0,
            address=trafficEntry.id,
            callsign=trafficEntry.callsign if trafficEntry.callsign is not None else "",
            navIntegrityCat=MessageConverter._getTrafficNavScore(trafficEntry),
            navAccuracyCat=MessageConverter._getTrafficNavScore(trafficEntry),
            emitterCat=GDL90EmitterCategory(trafficEntry.category) if trafficEntry.category is not None else GDL90EmitterCategory.no_info,
            trackIndicator=GDL90MiscellaneousIndicatorTrack.tt_true_track_angle,
            airborneIndicator=MessageConverter._getAirborneIndicator(trafficEntry.isOnGround),
        )

    def _secondsSinceMidnightUTC(datetime: datetime = datetime.utcnow()) -> int:
        if datetime is None:
            return None
        return (datetime.hour * 3600) + (datetime.minute * 60) + datetime.second

    def _getOwnshipNavScore(navMode: NavMode):
        # score to use for GDL90 nav integrity and accuracy
        if navMode == NavMode.Fix2D:
            return 5
        elif navMode == NavMode.Fix3D:
            return 9
        else:
            return 0

    def _getAirborneIndicator(onGround: bool) -> GDL90MiscellaneousIndicatorAirborne:
        if onGround is None:
            return GDL90MiscellaneousIndicatorAirborne.airborne
        elif onGround:
            return GDL90MiscellaneousIndicatorAirborne.on_ground
        else:
            return GDL90MiscellaneousIndicatorAirborne.airborne

    def _getTrafficNavScore(entry: TrafficEntry):
        if entry.latitude is None:
            return 0
        if entry.longitude is None:
            return 0
        if entry.groundSpeed is None:
            return 0
        if entry.verticalSpeed is None:
            return 0
        if entry.track is None:
            return 0
        else:
            return 10


class JsonSender:
    """
    used to periodically publish mqtt messages with monitored information
    """

    def __init__(self, navMonitor: NavMonitor, trafficMonitor: TrafficMonitor, gdl90Port: GDL90Port, messenger, sendIntervalSeconds):
        self._navMonitor = navMonitor
        self._trafficMonitor = trafficMonitor
        self._gdl90Port = gdl90Port
        self._messenger = messenger
        self._intervalSeconds = sendIntervalSeconds

    def start(self):
        self._sendMessages()

    def _sendMessages(self):
        try:
            self._timer = threading.Timer(self._intervalSeconds, self._sendMessages)
            self._timer.start()
            status = dict()
            status["gdl90"] = {
                "isActive": self._gdl90Port.isActive,
                "ip": self._gdl90Port.ip,
                "netMask": self._gdl90Port.netMask,
                "broadcastIp": self._gdl90Port.broadcastIp,
                "nic": self._gdl90Port.nic,
                "port": self._gdl90Port.port,
            }
            status = json.dumps(status)
            satellites = json.dumps(list(self._navMonitor.satellites.values()))
            traffic = json.dumps(list(self._trafficMonitor.traffic.values()))
            position = json.dumps(self._navMonitor.posInfo)
            self._messenger.sendNotification("/easyadsb/monitor/satellites", satellites)
            self._messenger.sendNotification("/easyadsb/monitor/traffic", traffic)
            self._messenger.sendNotification("/easyadsb/monitor/position", position)
            self._messenger.sendNotification("/easyadsb/monitor/status", status)

        except Exception as ex:
            log.error("error sending json messages, {}".format(str(ex)))


def main():
    logLevel = str(os.getenv("MO_LOG_LEVEL"))
    broker = str(os.getenv("MO_MQTT_HOST"))
    port = int(os.getenv("MO_MQTT_PORT"))
    clientName = str(os.getenv("MO_MQTT_CLIENT_NAME"))
    nmeaTopic = str(os.getenv("MO_MQTT_NMEA_TOPIC"))
    ubxTopic = str(os.getenv("MO_MQTT_UBX_TOPIC"))
    sbsTopic = str(os.getenv("MO_MQTT_SBS_TOPIC"))
    bmeTopic = str(os.getenv("MO_MQTT_BME280_TOPIC"))
    gdl90NetworkInterface = str(os.getenv("MO_GDL90_NETWORK_INTERFACE"))
    gdl90NetworkPort = int(os.getenv("MO_GDL90_PORT"))

    util.setupLogging(logLevel)
    atexit.register(onExit)

    with open("/home/data/mictronics/aircrafts.json") as f:
        aircrafts = json.load(f)
    with open("/home/data/mictronics/types.json") as f:
        types = json.load(f)
    with open("/home/data/mictronics/dbversion.json") as f:
        dbversion = json.load(f)
    with open("/home/data/typesExtension.json") as f:
        typesExtension = json.load(f)

    if clientName == "":
        log.info("mqtt client name is empty, assign uuid")
        clientName = str(uuid.uuid1())

    trafficMonitor = TrafficMonitor(aircrafts, types, dbversion["version"], typesExtension)
    navMonitor = NavMonitor()
    msgDispatcher = MessageDispatcher(navMonitor, trafficMonitor)
    log.debug("{name}, {broker}, {port}".format(name=clientName, broker=broker, port=port))
    mqttClient = mqtt.launch(clientName, broker, port)
    subscriptions = {
        nmeaTopic: {
            "type": mqtt.MqttMessenger.NOTIFICATION,
            "func": msgDispatcher.onNmeaMessage
        },
        ubxTopic: {
            "type": mqtt.MqttMessenger.NOTIFICATION,
            "func": msgDispatcher.onUbxMessage
        },
        sbsTopic: {
            "type": mqtt.MqttMessenger.NOTIFICATION,
            "func": msgDispatcher.onSbsMessage
        },
        bmeTopic: {
            "type": mqtt.MqttMessenger.NOTIFICATION,
            "func": msgDispatcher.onBmeMessage
        },
        "/easyadsb/monitor/traffic/ctrl": {
            "type": mqtt.MqttMessenger.REQUEST,
            "func": msgDispatcher.onTrafficRequest
        }
    }
    messenger = mqtt.MqttMessenger(mqttClient, subscriptions)
    gdl90Port = GDL90Port(gdl90NetworkInterface, gdl90NetworkPort)
    gdl90Sender = GDL90Sender(gdl90Port, navMonitor)
    jsonSender = JsonSender(navMonitor, trafficMonitor, gdl90Port, messenger, 1)
    jsonSender.start()
    trafficMonitor.register(gdl90Sender)
    navMonitor.register(gdl90Sender)
    gdl90Port.exec()


if __name__ == "__main__":
    main()
