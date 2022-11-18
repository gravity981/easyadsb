import logging
import paho.mqtt.client as mqtt
import uuid
import time
import atexit
import os
from pynmeagps import NMEAReader
import SBSReader
import Monitor

def setup_logging(level: str):
    fmt = '[%(asctime)s][%(levelname)-8s][%(filename)s:%(lineno)d] - %(message)s'
    if level == 'DEBUG':
        log_level = logging.DEBUG
    elif level == 'INFO':
        log_level = logging.INFO
    elif level == 'WARNING':
        log_level = logging.WARNING
    else:
        log_level = logging.WARNING
    logging.basicConfig(level=log_level, format=fmt)

def on_exit():
    global run
    if client is not None:
        client.loop_stop()
        client.disconnect()
    if logger is not None:
        logger.info('Exit application')
    run = False

def launch_mqtt(client_name, host, port) -> mqtt.Client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logger.info("mqtt connected")
        else:
            logger.warning('could not connect to mqtt server. code: %s', str(rc))

    def on_disconnect(client, userdata, rc):
        logger.info('disconnected from mqtt server, code: %s, userdata: %s', str(rc), str(userdata))

    client = mqtt.Client(client_name)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.connect(host, port, keepalive=60)
    client.loop_start()
    return client

def on_nmea_message(msg):
    try:
        nmea = NMEAReader.parse(msg)
        logger.debug(nmea)
    except Exception:
        logger.error("nmea message parse error")
        return

def on_sbs_message(msg):
    try:
        sbs = SBSReader.parse(msg)
        logger.debug(sbs)
    except Exception:
        logger.error("sbs message parse error")
        return
    trafficMonitor.update(sbs)
    
def on_message(client, userdata, msg):
    if msg.topic == nmea_topic:
        on_nmea_message(msg.payload.decode())
    elif msg.topic == sbs_topic:
        on_sbs_message(msg.payload.decode())
    else:
        logger.warning("message from unexpected topic \"{topic}\"".format(topic=msg.topic))


if __name__ == '__main__':
    logger = None
    client = None
    run = True
    trafficMonitor = Monitor.TrafficMonitor()

    logger_name="logger"
    log_level = str(os.getenv('GD_LOG_LEVEL', default='INFO'))

    broker = str(os.getenv('GD_MQTT_HOST', default='localhost'))
    port = int(os.getenv('GD_MQTT_PORT', default=1883))
    client_name = str(os.getenv('GD_MQTT_CLIENT_NAME'))
    nmea_topic = str(os.getenv('GD_MQTT_NMEA_TOPIC', default='/gps/nmea'))
    sbs_topic = str(os.getenv('GD_MQTT_SBS_TOPIC', default='/adsb/sbs'))
    publish_topic = str(os.getenv('GD_MQTT_PUBLISH_TOPIC', default='/gdl90'))

    setup_logging(log_level)
    logger = logging.getLogger(logger_name)
    atexit.register(on_exit)

    if client_name == "":
        logger.info("client_name is empty, assign uuid")
        client_name = str(uuid.uuid1())

    logger.debug("{client_name}, {broker}, {port}".format(client_name=client_name, broker=broker, port=port))
    client = launch_mqtt(client_name, broker, port)
    client.on_message = on_message
    client.subscribe(nmea_topic)
    client.subscribe(sbs_topic)
    while(run):
        logger.info("entries: {count}".format(count=len(trafficMonitor.traffic.keys())))
        for k, v in trafficMonitor.traffic.items():
            logger.info("id={id}, callsign={callsign}, lat={lat}, lon={lon}, alt={alt}, trk={trk}, spd={spd}"
            .format(id=v.id, callsign=v.callsign, lat=v.latitude, lon=v.longitude, alt=v.altitude, trk=v.track, spd=v.groundSpeed))
        time.sleep(10)