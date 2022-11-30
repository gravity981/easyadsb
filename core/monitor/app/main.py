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
        lock.acquire()
        heartbeat = gdl90.encodeHeartbeatMessage(
            gdl90.GDL90HeartBeatMessage(
                isInitialized=True,
                isLowBattery=False,
                time=gdl90.secondsSinceMidnightUTC(gpsMonitor.utcTime),
                posValid=gpsMonitor.navMode != pos.NavMode.NoFix,
            )
        )
        ownship = gdl90.encodeOwnshipMessage(
            gdl90.GDL90TrafficMessage(
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
                airborneIndicator=gdl90.GDL90MiscellaneousIndicatorAirborne.airborne,
            )
        )  # derive from speed
        ownship_alt = gdl90.encodeOwnshipAltitudeMessage(
            gdl90.GDL90OwnshipGeoAltitudeMessage(
                altitude=gpsMonitor.altitudeMeter * 3.28084 if gpsMonitor.altitudeMeter is not None else 0, merit=50, isWarning=False
            )
        )
        res = sock.sendto(heartbeat, (gdl90_broadcast_ip, gdl90_port))
        if res < 11:
            logger.warning("sent heartbytes bytes is too small. is socket ok?")
        sock.sendto(ownship, (gdl90_broadcast_ip, gdl90_port))
        sock.sendto(ownship_alt, (gdl90_broadcast_ip, gdl90_port))
        for k, v in trafficMonitor.traffic.items():
            if v.ready:
                traffic = gdl90.encodeTrafficMessage(
                    gdl90.GDL90TrafficMessage(
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
                )
                res = sock.sendto(traffic, (gdl90_broadcast_ip, gdl90_port))
    finally:
        lock.release()


def socket_health_check():
    # health check is realised by continously reading back broadcast data and checking for socket timeout
    # timeout indicates that socket does not work anymore and has to be recreated
    global sock
    while True:
        try:
            # returns up to N bytes, can return less, is blocking if there is no data to read from the socket,
            # could be made non-blocking (beware of exceptions in this case)
            data = sock.recv(1000)
            if len(data) <= 0:
                raise ValueError('received unexpected "{}" number of bytes'.format(len(data)))
        except (TimeoutError, ValueError) as e:
            logger.error('detected problem with socket "{}", recreate socket...'.format(str(e)))
            with lock:
                init_socket()


def init_socket():
    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(2)
    # bind the sockeet to make sure periodic udp broadcast stays alive
    sock.bind((gdl90_broadcast_ip, gdl90_port))


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
    init_socket()
    tl.start()
    lock = threading.Lock()
    thread = threading.Thread(target=socket_health_check)
    thread.start()
