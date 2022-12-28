import logging as log
import uuid
import atexit
import os
from pyubx2 import UBXReader
from pynmeagps import NMEAReader
from sbs import SBSReader
import positioning as pos
import traffic as traffic
import gdl90
from datetime import datetime
import threading
import json
import sysinfo

try:
    import common.mqtt as mqtt
    import common.logconf as logconf
except ImportError:
    import mqtt
    import logconf


def on_exit():
    log.info("Exit application")
    # if mqttClient is not None:
    #    mqttClient.loop_stop()
    #    mqttClient.disconnect()
    # if trafficMonitor is not None:
    #    trafficMonitor.stopAutoCleanup()


class MessageDispatcher:

    def __init__(self, gpsMonitor, trafficMonitor):
        self._gpsMonitor = gpsMonitor
        self._trafficMonitor = trafficMonitor

    def onMessage(self, client, userdata, msg):
        if "nmea" in msg.topic:
            self._onNmeaMessage(msg)
        elif "ubx" in msg.topic:
            self._onUbxMessage(msg)
        elif "sbs" in msg.topic:
            self._onSbsMessage(msg)
        elif "bme" in msg.topic:
            self._onBmeMessage(msg)
        else:
            log.warning('message from unexpected topic "{topic}"'.format(topic=msg.topic))

    def _onNmeaMessage(self, msg):
        try:
            nmea = NMEAReader.parse(msg.payload)
            log.debug(nmea)
            self._gpsMonitor.update(nmea)
        except Exception as ex:
            log.error('on nmea message error, {}, "{}"'.format(str(ex), msg.payload))
            return

    def _onUbxMessage(self, msg):
        try:
            ubx = UBXReader.parse(msg.payload)
            log.debug(ubx)
        except Exception as ex:
            log.error('on ubx message error, {}, "{}"'.format(str(ex), msg.payload))
            return

    def _onSbsMessage(self, msg):
        try:
            dec = msg.payload.decode("UTF-8").strip()
            sbs = SBSReader.parse(dec)
            log.debug(sbs)
            self._trafficMonitor.update(sbs)
        except UnicodeDecodeError:
            log.error('on sbs message payload decode error, "{}"'.format(msg.payload))
            return
        except Exception as ex:
            log.error('on sbs message error, {}, "{}"'.format(str(ex), msg.payload))
            return

    def _onBmeMessage(self, msg):
        try:
            bme = json.loads(msg.payload.decode("UTF-8").strip())
            log.debug(bme)
            self._gpsMonitor.updateBme(bme)
        except Exception as ex:
            log.error('on bme message error, {}, "{}"'.format(str(ex), msg.payload))
            return


class GDL90Sender:
    """
    used to send various GDL90 messages to a `GDL90Port`.
    Manages periodic GDL90 Heartbeat.
    """

    def __init__(self, gdl90Port: gdl90.GDL90Port, gpsMonitor):
        self._gdl90Port = gdl90Port
        self._heartbeatIntervalSeconds = 1
        self._gpsMonitor = gpsMonitor
        self._sendHeartbeatMsg()

    def send(self, msg):
        if self._gdl90Port.isActive:
            self._gdl90Port.putMessage(msg)

    def _sendHeartbeatMsg(self):
        try:
            self._timer = threading.Timer(self._heartbeatIntervalSeconds, self._sendHeartbeatMsg)
            self._timer.start()
            heartbeat = MessageConverter.toGDL90HeartbeatMsg(self._gpsMonitor.posInfo)
            self.send(heartbeat)
        except Exception as ex:
            log.error("error sending gdl90 heartbeat message, {}".format(str(ex)))


class MessageConverter:
    """
    static class to convert & create different types of messages.
    Can get notified with `TrafficEntry` or `NavMonitor` objects.
    """
    # todo make this a static class
    def __init__(self, gdl90Sender: GDL90Sender):
        self._gdl90Sender = gdl90Sender

    # todo move function to gdlsender
    def notify(self, obj):
        if type(obj) == traffic.TrafficEntry:
            trafficMsg = MessageConverter.toGDL90TrafficMsg(obj)
            self._gdl90Sender.send(trafficMsg)
        elif type(obj) == pos.PosInfo:
            ownshipMsg = MessageConverter.toGDL90OwnshipMsg(obj)
            ownshipAltMsg = MessageConverter.toGDL90OwnshipGeoAltMsg(obj)
            self._gdl90Sender.send(ownshipMsg)
            self._gdl90Sender.send(ownshipAltMsg)
        else:
            log.error("notified with unexpected object of type {}".format(type(obj)))

    def toGDL90OwnshipMsg(posInfo: pos.PosInfo):
        return gdl90.GDL90OwnshipMessage(
            latitude=posInfo.latitude if posInfo.latitude is not None else 0,
            longitude=posInfo.longitude if posInfo.longitude is not None else 0,
            altitude=posInfo.altitudeMeter * 3.28084 if posInfo.altitudeMeter is not None else 0,
            hVelocity=int(posInfo.groundSpeedKnots) if posInfo.groundSpeedKnots is not None else 0,
            vVelocity=0,
            trackHeading=posInfo.trueTrack if posInfo.trueTrack is not None else 0,
            navIntegrityCat=MessageConverter._getOwnshipNavScore(posInfo.navMode),
            navAccuracyCat=MessageConverter._getOwnshipNavScore(posInfo.navMode),
            emitterCat=gdl90.GDL90EmitterCategory.light,
            trackIndicator=gdl90.GDL90MiscellaneousIndicatorTrack.tt_true_track_angle,
            airborneIndicator=gdl90.GDL90MiscellaneousIndicatorAirborne.airborne,
        )

    def toGDL90OwnshipGeoAltMsg(posInfo: pos.PosInfo):
        return gdl90.GDL90OwnshipGeoAltitudeMessage(
            altitude=posInfo.altitudeMeter * 3.28084 if posInfo.altitudeMeter is not None else 0, merit=50, isWarning=False
        )

    def toGDL90HeartbeatMsg(posInfo: pos.PosInfo):
        seconds = MessageConverter._secondsSinceMidnightUTC(posInfo.utcTime)
        return gdl90.GDL90HeartBeatMessage(
            isInitialized=seconds is not None,
            isLowBattery=False,
            time=seconds if seconds is not None else 0,
            posValid=posInfo.navMode != pos.NavMode.NoFix,
        )

    def toGDL90TrafficMsg(trafficEntry: traffic.TrafficEntry):
        return gdl90.GDL90TrafficMessage(
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
            emitterCat=gdl90.GDL90EmitterCategory(trafficEntry.category) if trafficEntry.category is not None else gdl90.GDL90EmitterCategory.no_info,
            trackIndicator=gdl90.GDL90MiscellaneousIndicatorTrack.tt_true_track_angle,
            airborneIndicator=MessageConverter._getAirborneIndicator(trafficEntry.isOnGround),
        )

    def _secondsSinceMidnightUTC(datetime: datetime = datetime.utcnow()) -> int:
        if datetime is None:
            return None
        return (datetime.hour * 3600) + (datetime.minute * 60) + datetime.second

    def _getOwnshipNavScore(navMode: pos.NavMode):
        # score to use for GDL90 nav integrity and accuracy
        if navMode == pos.NavMode.Fix2D:
            return 5
        elif navMode == pos.NavMode.Fix3D:
            return 9
        else:
            return 0

    def _getAirborneIndicator(onGround: bool) -> gdl90.GDL90MiscellaneousIndicatorAirborne:
        if onGround is None:
            return gdl90.GDL90MiscellaneousIndicatorAirborne.airborne
        elif onGround:
            return gdl90.GDL90MiscellaneousIndicatorAirborne.on_ground
        else:
            return gdl90.GDL90MiscellaneousIndicatorAirborne.airborne

    def _getTrafficNavScore(entry: traffic.TrafficEntry):
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
    used to periodically send traffic and position messages to mqtt topic
    """

    def __init__(self, navMonitor: pos.NavMonitor, trafficMonitor: traffic.TrafficMonitor, gdl90Port: gdl90.GDL90Port, mqttClient, sendIntervalSeconds):
        self._navMonitor = navMonitor
        self._trafficMonitor = trafficMonitor
        self._gdl90Port = gdl90Port
        self._mqttClient = mqttClient
        self._intervalSeconds = sendIntervalSeconds

    def start(self):
        self._sendMessages()

    def _sendMessages(self):
        try:
            self._timer = threading.Timer(self._intervalSeconds, self._sendMessages)
            self._timer.start()
            system = dict()
            system["wifi"] = sysinfo.Wifi.parseIwConfig(sysinfo.Wifi.getIwConfig(self._gdl90Port.nic))
            system["gdl90"] = {
                "isActive": self._gdl90Port.isActive,
                "ip": self._gdl90Port.ip,
                "netMask": self._gdl90Port.netMask,
                "broadcastIp": self._gdl90Port.broadcastIp,
                "nic": self._gdl90Port.nic,
                "port": self._gdl90Port.port,
            }
            system["resources"] = sysinfo.Resources.parseMemInfo(sysinfo.Resources.getMemInfoFromProcfs())
            system["resources"]["cpuTemp"] = sysinfo.Resources.parseCpuTemperature(sysinfo.Resources.getCpuTempFromSysfs())
            system["resources"]["cpuUsage"] = sysinfo.Resources.parseCpuUsage(sysinfo.Resources.getStatFromProcfs())
            system = json.dumps(system)
            satellites = json.dumps(list(self._navMonitor.satellites.values()))
            traffic = json.dumps(list(self._trafficMonitor.traffic.values()))
            position = json.dumps(self._navMonitor.posInfo)
            self._mqttClient.publish("/easyadsb/monitor/satellites", satellites)
            self._mqttClient.publish("/easyadsb/monitor/traffic", traffic)
            self._mqttClient.publish("/easyadsb/monitor/position", position)
            self._mqttClient.publish("/easyadsb/monitor/system", system)

        except Exception as ex:
            log.error("error sending json messages, {}".format(str(ex)))


def main():
    mqttClient = None
    log_level = str(os.getenv("MO_LOG_LEVEL"))
    broker = str(os.getenv("MO_MQTT_HOST"))
    port = int(os.getenv("MO_MQTT_PORT"))
    client_name = str(os.getenv("MO_MQTT_CLIENT_NAME"))
    nmea_topic = str(os.getenv("MO_MQTT_NMEA_TOPIC"))
    ubx_topic = str(os.getenv("MO_MQTT_UBX_TOPIC"))
    sbs_topic = str(os.getenv("MO_MQTT_SBS_TOPIC"))
    bme_topic = str(os.getenv("MO_MQTT_BME280_TOPIC"))
    gdl90_network_interface = str(os.getenv("MO_GDL90_NETWORK_INTERFACE"))
    gdl90_port = int(os.getenv("MO_GDL90_PORT"))

    logconf.setup_logging(log_level)
    atexit.register(on_exit)

    with open("/home/data/mictronics/aircrafts.json") as json_file:
        aircrafts = json.load(json_file)
    with open("/home/data/mictronics/types.json") as json_file:
        types = json.load(json_file)
    with open("/home/data/mictronics/dbversion.json") as json_file:
        dbversion = json.load(json_file)
    with open("/home/data/typesExtension.json") as json_file:
        typesExtension = json.load(json_file)

    if client_name == "":
        log.info("client_name is empty, assign uuid")
        client_name = str(uuid.uuid1())

    trafficMonitor = traffic.TrafficMonitor(aircrafts, types, dbversion, typesExtension)
    trafficMonitor.startAutoCleanup()
    gpsMonitor = pos.NavMonitor()
    msgDispatcher = MessageDispatcher(gpsMonitor, trafficMonitor)
    log.debug("{client_name}, {broker}, {port}".format(client_name=client_name, broker=broker, port=port))
    mqttClient = mqtt.launch(client_name, broker, port, [nmea_topic, ubx_topic, sbs_topic, bme_topic], msgDispatcher.onMessage)
    gdl90Port = gdl90.GDL90Port(gdl90_network_interface, gdl90_port)
    gdl90Sender = GDL90Sender(gdl90Port, gpsMonitor)
    msgConverter = MessageConverter(gdl90Sender)
    jsonSender = JsonSender(gpsMonitor, trafficMonitor, gdl90Port, mqttClient, 1)
    jsonSender.start()
    trafficMonitor.register(msgConverter)
    gpsMonitor.register(msgConverter)
    gdl90Port.exec()


if __name__ == "__main__":
    main()
