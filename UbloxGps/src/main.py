from serial import Serial
from pyubx2 import UBXReader, UBXMessage
from pynmeagps import NMEAMessage
import logging
import atexit
import os
import SimpleMqttClient
import uuid

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
    if logger is not None:
        logger.info('Exit application')
    if client is not None:
        client.disconnect()
    run = False

def run_serial_publish(mqtt, ubr: UBXReader):
    while(run):
        (raw_data, parsed_data) = ubr.read()
        logger.debug(parsed_data)
        if type(parsed_data) == UBXMessage:
            client.publish(publish_topic_ubx, raw_data) 
        if type(parsed_data) == NMEAMessage:
            client.publish(publish_topic_nmea, raw_data) 

if __name__ == '__main__':
    logger = None
    client = None
    run = True

    logger_name="logger"
    log_level = str(os.getenv('UB_LOG_LEVEL'))
    serial_device = str(os.getenv('UB_SERIAL_DEVICE'))
    serial_baud = int(os.getenv('UB_SERIAL_BAUD'))
    broker = str(os.getenv('UB_MQTT_HOST'))
    port = int(os.getenv('UB_MQTT_PORT'))
    client_name = str(os.getenv('UB_MQTT_CLIENT_NAME'))
    publish_topic_ubx = str(os.getenv('UB_MQTT_UBX_PUBLISH_TOPIC'))
    publish_topic_nmea = str(os.getenv('UB_MQTT_NMEA_PUBLISH_TOPIC'))

    setup_logging(log_level)
    logger = logging.getLogger(logger_name)
    atexit.register(on_exit)

    if client_name == "":
        logger.info("client_name is empty, assign uuid")
        client_name = str(uuid.uuid1())

    client = SimpleMqttClient.SimpleMqttClient(broker, port, 60, client_name, logger_name)
    if not client.connect():
        exit()

    stream = Serial(serial_device, serial_baud, timeout=3)
    ubr = UBXReader(stream)
    logger.info("start publishing UBX messages from \"{device}\" to {topic}".format(device=serial_device, topic=publish_topic_ubx))
    logger.info("start publishing NMEA messages from \"{device}\" to {topic}".format(device=serial_device, topic=publish_topic_nmea))
    run_serial_publish(client, ubr)

    exit()
    

