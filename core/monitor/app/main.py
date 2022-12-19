import logging
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
    if logger is not None:
        logger.info("Exit application")
    if mqttClient is not None:
        mqttClient.loop_stop()
        mqttClient.disconnect()
    if trafficMonitor is not None:
        trafficMonitor.stopAutoCleanup()


def on_nmea_message(msg):
    try:
        nmea = NMEAReader.parse(msg.payload)
        logger.debug(nmea)
        gpsMonitor.update(nmea)
    except Exception as ex:
        logger.error('on nmea message error, {}, "{}"'.format(str(ex), msg.payload))
        return


def on_ubx_message(msg):
    try:
        ubx = UBXReader.parse(msg.payload)
        logger.debug(ubx)
    except Exception as ex:
        logger.error('on ubx message error, {}, "{}"'.format(str(ex), msg.payload))
        return


def on_sbs_message(msg):
    try:
        dec = msg.payload.decode("UTF-8").strip()
        sbs = SBSReader.parse(dec)
        logger.debug(sbs)
        trafficMonitor.update(sbs)
    except UnicodeDecodeError:
        logger.error('on sbs message payload decode error, "{}"'.format(msg.payload))
        return
    except Exception as ex:
        logger.error('on sbs message error, {}, "{}"'.format(str(ex), msg.payload))
        return


def on_bme_message(msg):
    try:
        bme = json.loads(msg.payload.decode("UTF-8").strip())
        logger.debug(bme)
        gpsMonitor.updateBme(bme)
    except Exception as ex:
        logger.error('on bme message error, {}, "{}"'.format(str(ex), msg.payload))
        return


def on_message(client, userdata, msg):
    if msg.topic == nmea_topic:
        on_nmea_message(msg)
    elif msg.topic == ubx_topic:
        on_ubx_message(msg)
    elif msg.topic == sbs_topic:
        on_sbs_message(msg)
    elif msg.topic == bme_topic:
        on_bme_message(msg)
    else:
        logger.warning('message from unexpected topic "{topic}"'.format(topic=msg.topic))


class GDL90Sender:
    """
    used to send various GDL90 messages to a `GDL90Port`.
    Manages periodic GDL90 Heartbeat.
    """

    def __init__(self, gdl90Port: gdl90.GDL90Port):
        self._gdl90Port = gdl90Port
        self._heartbeatIntervalSeconds = 1
        self._sendHeartbeatMsg()

    def send(self, msg):
        self._gdl90Port.putMessage(msg)

    def _sendHeartbeatMsg(self):
        try:
            self._timer = threading.Timer(self._heartbeatIntervalSeconds, self._sendHeartbeatMsg)
            self._timer.start()
            heartbeat = MessageConverter.toGDL90HeartbeatMsg(gpsMonitor.posInfo)
            self._gdl90Port.putMessage(heartbeat)
        except Exception as ex:
            logger.error("error sending gdl90 heartbeat message, {}".format(str(ex)))


class MessageConverter:
    """
    static class to convert & create different types of messages.
    Can get notified with `TrafficEntry` or `NavMonitor` objects.
    """

    def __init__(self, gdl90Sender: GDL90Sender):
        self._gdl90Sender = gdl90Sender

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
            logger.error("notified with unexpected object of type {}".format(type(obj)))

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
            emitterCat=gdl90.GDL90EmitterCategory.light,  # make configurable
            trackIndicator=gdl90.GDL90MiscellaneousIndicatorTrack.tt_true_track_angle,  # derive from infromation from gps
            airborneIndicator=gdl90.GDL90MiscellaneousIndicatorAirborne.airborne,  # derive from speed
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


def getWifiInfo():
    return sysinfo.Wifi.parseIwConfig(sysinfo.Wifi.getIwConfig(gdl90_network_interface))


class JsonSender:
    """
    used to periodically send traffic and position messages to mqtt topic
    """

    def __init__(self, navMonitor: pos.NavMonitor, trafficMonitor: traffic.TrafficMonitor, mqttClient):
        self._navMonitor = navMonitor
        self._trafficMonitor = trafficMonitor
        self._mqttClient = mqttClient
        self._intervalSeconds = 5
        self._sendMessages()

    def _sendMessages(self):
        try:
            self._timer = threading.Timer(self._intervalSeconds, self._sendMessages)
            self._timer.start()
            """
            - x wifi state (ap associated)
            - x wifi name
            - x wifi signal strength
            - x gdl 90 status "GDL90Port.isActive"
            - x ip addr + mask + port + broadcast + nic --> from GDL90Port
            - gps alive
            - bme280 alive
            - cpu temperature --> cat /sys/class/thermal/thermal_zone0/temp (access?)
            - memory usage --> cat /proc/meminfo
            - cpu usage (5 min average) --> cat /proc/stat + calc over time
            """
            system = dict()
            system["wifi"] = getWifiInfo()
            system = json.dumps(system)

            satellites = json.dumps(list(self._navMonitor.satellites.values()))
            traffic = json.dumps(list(self._trafficMonitor.traffic.values()))
            position = json.dumps(self._navMonitor.posInfo)
            self._mqttClient.publish("/easyadsb/json/satellites", satellites)
            self._mqttClient.publish("/easyadsb/json/traffic", traffic)
            self._mqttClient.publish("/easyadsb/json/position", position)
            self._mqttClient.publish("/easyadsb/json/system", system)

        except Exception as ex:
            logger.error("error sending json messages, {}".format(str(ex)))


if __name__ == "__main__":
    logger = None
    mqttClient = None

    logger_name = "logger"
    log_level = str(os.getenv("MO_LOG_LEVEL"))

    broker = str(os.getenv("MO_MQTT_HOST"))
    port = int(os.getenv("MO_MQTT_PORT"))
    client_name = str(os.getenv("MO_MQTT_CLIENT_NAME"))
    nmea_topic = str(os.getenv("MO_MQTT_NMEA_TOPIC"))
    ubx_topic = str(os.getenv("MO_MQTT_UBX_TOPIC"))
    ubx_ctrl_topic = str(os.getenv("MO_MQTT_UBX_CTRL_TOPIC"))
    sbs_topic = str(os.getenv("MO_MQTT_SBS_TOPIC"))
    bme_topic = str(os.getenv("MO_MQTT_BME280_TOPIC"))
    gdl90_network_interface = str(os.getenv("MO_GDL90_NETWORK_INTERFACE"))
    gdl90_port = int(os.getenv("MO_GDL90_PORT"))

    logconf.setup_logging(log_level)
    logger = logging.getLogger(logger_name)
    atexit.register(on_exit)

    with open("/home/data/aircrafts.json") as json_file:
        aircrafts = json.load(json_file)
    with open("/home/data/models.json") as json_file:
        models = json.load(json_file)

    if client_name == "":
        logger.info("client_name is empty, assign uuid")
        client_name = str(uuid.uuid1())

    trafficMonitor = traffic.TrafficMonitor(aircrafts, models)
    trafficMonitor.startAutoCleanup()
    gpsMonitor = pos.NavMonitor()
    logger.debug("{client_name}, {broker}, {port}".format(client_name=client_name, broker=broker, port=port))
    mqttClient = mqtt.launch(client_name, broker, port)
    mqttClient.on_message = on_message
    mqttClient.subscribe(nmea_topic)
    mqttClient.subscribe(ubx_topic)
    mqttClient.subscribe(sbs_topic)
    mqttClient.subscribe(bme_topic)
    gdl90Port = gdl90.GDL90Port(gdl90_network_interface, gdl90_port)
    gdl90Sender = GDL90Sender(gdl90Port)
    msgConverter = MessageConverter(gdl90Sender)
    jsonSender = JsonSender(gpsMonitor, trafficMonitor, mqttClient)
    trafficMonitor.register(msgConverter)
    gpsMonitor.register(msgConverter)
    gdl90Port.exec()
