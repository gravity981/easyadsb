import logging
import uuid
import time
import atexit
import os
from pyubx2 import UBXReader
from pynmeagps import NMEAReader
import SBSProtocol
import monitor
import socket
import GDL90Protocol as gdl
from datetime import datetime

try:
    import common.mqtt as mqtt
    import common.logconf as logconf
except ImportError:
    import mqtt
    import logconf


def on_exit():
    global run
    if client is not None:
        client.loop_stop()
        client.disconnect()
    if logger is not None:
        logger.info("Exit application")
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
        sbs = SBSProtocol.parse(dec)
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


if __name__ == "__main__":
    logger = None
    client = None
    run = True

    trafficMonitor = monitor.TrafficMonitor()
    gpsMonitor = monitor.GpsMonitor()

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
    atexit.register(on_exit)

    if client_name == "":
        logger.info("client_name is empty, assign uuid")
        client_name = str(uuid.uuid1())

    logger.debug("{client_name}, {broker}, {port}".format(client_name=client_name, broker=broker, port=port))
    client = mqtt.launch(client_name, broker, port)
    client.on_message = on_message
    client.subscribe(nmea_topic)
    client.subscribe(ubx_topic)
    client.subscribe(sbs_topic)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    while run:
        heartbeat = gdl.encodeHeartbeatMessage(gdl.GDL90HeartBeatMessage(time=gdl.secondsSinceMidnightUTC(datetime.utcnow())))
        ownship = gdl.encodeOwnshipMessage(
            gdl.GDL90TrafficMessage(
                latitude=46.912222,  # get from gps
                longitude=7.499167,  # get from gps
                altitude=5000,  # calculate from barometric pressure
                hVelocity=50,  # get from gps
                vVelocity=0,  # get from gps
                trackHeading=90,  # get from gps
                navIntegrityCat=8,  # derive from infromation from gps
                navAccuracyCat=9,  # derive from infromation from gps
                emitterCat=gdl.GDL90EmitterCategory.light,  # make configurable
                trackIndicator=gdl.GDL90MiscellaneousIndicatorTrack.tt_true_track_angle,  # derive from infromation from gps
                airborneIndicator=gdl.GDL90MiscellaneousIndicatorAirborne.airborne,
            )
        )  # derive from speed
        ownship_alt = gdl.encodeOwnshipAltitudeMessage(
            gdl.GDL90OwnshipGeoAltitudeMessage(altitude=5000, merit=50, isWarning=False)  # get from gps  # get from gps
        )  # derive from information from gps
        sock.sendto(heartbeat, (gdl90_broadcast_ip, gdl90_port))
        sock.sendto(ownship, (gdl90_broadcast_ip, gdl90_port))
        sock.sendto(ownship_alt, (gdl90_broadcast_ip, gdl90_port))
        for k, v in trafficMonitor.traffic.items():
            logger.debug(
                "id={id:X}, cs={callsign}, lat={lat}, lon={lon}, alt={alt}, trk={trk}, spd={spd}, cnt={cnt}".format(
                    id=v.id,
                    callsign=v.callsign,
                    lat=v.latitude,
                    lon=v.longitude,
                    alt=v.altitude,
                    trk=v.track,
                    spd=v.groundSpeed,
                    cnt=v.msgCount,
                )
            )
            if v.ready():
                traffic = gdl.encodeTrafficMessage(
                    gdl.GDL90TrafficMessage(
                        latitude=v.latitude,
                        longitude=v.longitude,
                        altitude=v.altitude,
                        hVelocity=v.groundSpeed,
                        vVelocity=0,
                        trackHeading=v.track,
                        address=v.id,
                        callsign=v.callsign,
                        navIntegrityCat=8,
                        navAccuracyCat=9,
                        emitterCat=v.category if v.category is not None else gdl.GDL90EmitterCategory.no_info,
                        trackIndicator=gdl.GDL90MiscellaneousIndicatorTrack.tt_true_track_angle,
                        airborneIndicator=gdl.GDL90MiscellaneousIndicatorAirborne.airborne,
                    )
                )
                sock.sendto(traffic, (gdl90_broadcast_ip, gdl90_port))
        time.sleep(1)
