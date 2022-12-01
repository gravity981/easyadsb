import logging
import uuid
import atexit
import os
from pyubx2 import UBXReader
from pynmeagps import NMEAReader
from sbs import SBSReader
import positioning as pos
import traffic as traffic
import socket
import gdl90
from datetime import timedelta
from timeloop import Timeloop
import threading
import json
import queue

try:
    import common.mqtt as mqtt
    import common.logconf as logconf
except ImportError:
    import mqtt
    import logconf


tl = Timeloop()


def on_exit():
    global run
    tl.stop()
    if client is not None:
        client.loop_stop()
        client.disconnect()
    if logger is not None:
        logger.info("Exit application")
    if trafficMonitor is not None:
        trafficMonitor.stopAutoCleanup()
    run = False


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
        logger.error('on sbs message error, {}, "{}"'.format(str(ex), dec))
        return


def on_message(client, userdata, msg):
    if msg.topic == nmea_topic:
        on_nmea_message(msg)
    elif msg.topic == ubx_topic:
        on_ubx_message(msg)
    elif msg.topic == sbs_topic:
        on_sbs_message(msg)
    else:
        logger.warning('message from unexpected topic "{topic}"'.format(topic=msg.topic))


# TODO move to dedicated converter class
def getNavScore():
    # score to use for GDL90 nav integrity and accuracy
    if gpsMonitor.navMode == pos.NavMode.Fix2D:
        return 5
    elif gpsMonitor.navMode == pos.NavMode.Fix3D:
        return 9
    else:
        return 0


# TODO move to dedicated converter class
def getAirborneIndicator(onGround: bool) -> gdl90.GDL90MiscellaneousIndicatorAirborne:
    if onGround is None:
        return gdl90.GDL90MiscellaneousIndicatorAirborne.airborne
    elif onGround:
        return gdl90.GDL90MiscellaneousIndicatorAirborne.on_ground
    else:
        return gdl90.GDL90MiscellaneousIndicatorAirborne.airborne


# TODO move dispatching of GDL90 messages into dedicated class.
# this class should observe changes of NavMonitor and TrafficMonitor
# TODO move message construction logic to dedicated converter class
@tl.job(interval=timedelta(seconds=1))
def send_gdl90_messages():
    try:
        heartbeat = gdl90.GDL90HeartBeatMessage(
            isInitialized=True,
            isLowBattery=False,
            time=gdl90.secondsSinceMidnightUTC(gpsMonitor.utcTime),
            posValid=gpsMonitor.navMode != pos.NavMode.NoFix,
        )

        ownship = gdl90.GDL90OwnshipMessage(
            latitude=gpsMonitor.latitude if gpsMonitor.latitude is not None else 0,
            longitude=gpsMonitor.longitude if gpsMonitor.longitude is not None else 0,
            altitude=gpsMonitor.altitudeMeter * 3.28084 if gpsMonitor.altitudeMeter is not None else 0,
            hVelocity=int(gpsMonitor.groundSpeedKnots) if gpsMonitor.groundSpeedKnots is not None else 0,
            vVelocity=0,
            trackHeading=gpsMonitor.trueTrack if gpsMonitor.trueTrack is not None else 0,
            navIntegrityCat=getNavScore(),
            navAccuracyCat=getNavScore(),
            emitterCat=gdl90.GDL90EmitterCategory.light,  # make configurable
            trackIndicator=gdl90.GDL90MiscellaneousIndicatorTrack.tt_true_track_angle,  # derive from infromation from gps
            airborneIndicator=gdl90.GDL90MiscellaneousIndicatorAirborne.airborne,  # derive from speed
        )

        ownship_alt = gdl90.GDL90OwnshipGeoAltitudeMessage(
            altitude=gpsMonitor.altitudeMeter * 3.28084 if gpsMonitor.altitudeMeter is not None else 0, merit=50, isWarning=False
        )

        gdl90Port.sendMessage(heartbeat)
        gdl90Port.sendMessage(ownship)
        gdl90Port.sendMessage(ownship_alt)
        for k, v in trafficMonitor.traffic.items():
            if v.ready:
                traffic = gdl90.GDL90TrafficMessage(
                    latitude=v.latitude,
                    longitude=v.longitude,
                    altitude=v.altitude,
                    hVelocity=v.groundSpeed,
                    vVelocity=v.verticalSpeed,
                    trackHeading=v.track,
                    address=v.id,
                    callsign=v.callsign,
                    navIntegrityCat=8,
                    navAccuracyCat=9,
                    emitterCat=v.category if v.category is not None else gdl90.GDL90EmitterCategory.no_info,
                    trackIndicator=gdl90.GDL90MiscellaneousIndicatorTrack.tt_true_track_angle,
                    airborneIndicator=getAirborneIndicator(v.isOnGround),
                )
                gdl90Port.sendMessage(traffic)
    finally:
        pass


class GDL90Port:
    def __init__(self):
        self._socket = None
        self._lock = threading.Lock()
        self._sendThread = threading.Thread(target=self._send, name="GDL90Sender")
        self._recvThread = threading.Thread(target=self._recv, name="GDL90Receiver")
        self._queue = queue.Queue()
        self._initSocket()

    def start(self):
        self._sendThread.start()
        self._recvThread.start()

    def stop(self):
        self._queue.join()
        self._sendThread.join()
        self._recvThread.join()

    def sendMessage(self, msg):
        self._queue.put(msg)

    def _initSocket(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._socket.settimeout(2)
        # bind the socket to readback broadcast packages for health check purposes
        self._socket.bind((gdl90_broadcast_ip, gdl90_port))

    def _send(self):
        # runs on thread
        while True:
            try:
                self._lock.acquire()
                msg = self._queue.get()
                if type(msg) == gdl90.GDL90HeartBeatMessage:
                    bytes = gdl90.encodeHeartbeatMessage(msg)
                elif type(msg) == gdl90.GDL90TrafficMessage:
                    bytes = gdl90.encodeTrafficMessage(msg)
                elif type(msg) == gdl90.GDL90OwnshipMessage:
                    bytes = gdl90.encodeOwnshipMessage(msg)
                elif type(msg) == gdl90.GDL90OwnshipGeoAltitudeMessage:
                    bytes = gdl90.encodeOwnshipAltitudeMessage(msg)
                else:
                    raise TypeError("msg has unexpected type {}".format(type(msg)))
                self._socket.sendto(bytes, (gdl90_broadcast_ip, gdl90_port))
            except Exception as e:
                logger.error("error sending gdl90 message, {}".format(str(e)))
            finally:
                self._queue.task_done()
                self._lock.release()

    def _recv(self):
        # runs on thread
        # continously read back broadcast data and checking for socket timeout
        # timeout indicates that socket does not work anymore and has to be recreated
        while True:
            try:
                # returns up to N bytes, can return less, is blocking if there is no data to read from the socket,
                # could be made non-blocking (beware of exceptions in this case)
                data = self._socket.recv(1000)
                if len(data) <= 0:
                    raise ValueError('received unexpected "{}" number of bytes'.format(len(data)))
            except (TimeoutError, ValueError) as e:
                logger.error('detected problem with socket "{}", recreate socket...'.format(str(e)))
                with self._lock:
                    self._initSocket()


if __name__ == "__main__":
    logger = None
    client = None

    logger_name = "logger"
    log_level = str(os.getenv("MO_LOG_LEVEL"))

    broker = str(os.getenv("MO_MQTT_HOST"))
    port = int(os.getenv("MO_MQTT_PORT"))
    client_name = str(os.getenv("MO_MQTT_CLIENT_NAME"))
    nmea_topic = str(os.getenv("MO_MQTT_NMEA_TOPIC"))
    ubx_topic = str(os.getenv("MO_MQTT_UBX_TOPIC"))
    ubx_ctrl_topic = str(os.getenv("MO_MQTT_UBX_CTRL_TOPIC"))
    sbs_topic = str(os.getenv("MO_MQTT_SBS_TOPIC"))
    gdl90_broadcast_ip = str(os.getenv("MO_GDL90_BROADCAST_IP"))
    gdl90_port = int(os.getenv("MO_GDL90_PORT"))

    logconf.setup_logging(log_level)
    logger = logging.getLogger(logger_name)
    tl.logger = logger
    atexit.register(on_exit)

    with open("/home/data/aircrafts.json") as json_file:
        aircrafts = json.load(json_file)
    with open("/home/data/models.json") as json_file:
        models = json.load(json_file)

    trafficMonitor = traffic.TrafficMonitor(aircrafts, models)
    gpsMonitor = pos.NavMonitor()
    trafficMonitor.startAutoCleanup()

    if client_name == "":
        logger.info("client_name is empty, assign uuid")
        client_name = str(uuid.uuid1())

    logger.debug("{client_name}, {broker}, {port}".format(client_name=client_name, broker=broker, port=port))
    client = mqtt.launch(client_name, broker, port)
    client.on_message = on_message
    client.subscribe(nmea_topic)
    client.subscribe(ubx_topic)
    client.subscribe(sbs_topic)
    gdl90Port = GDL90Port()
    gdl90Port.start()

    tl.start()
