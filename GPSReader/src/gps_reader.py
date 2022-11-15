from serial import Serial
from pynmeagps import NMEAReader
import logging
import atexit
import os
import SimpleMqttClient

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


if __name__ == '__main__':
    logger = None
    client = None
    run = True
    log_level = str(os.getenv('GR_LOG_LEVEL', default='INFO'))
    serial_device = str(os.getenv('GR_SERIAL_DEVICE', default='/dev/ttyAMA0'))
    broker = str(os.getenv('GR_MQTT_HOST', default='localhost'))
    port = int(os.getenv('GR_MQTT_PORT', default=1883))
    client_name = str(os.getenv('GR_MQTT_CLIENT_NAME', default='gps_reader'))
    publish_topic = str(os.getenv('GR_MQTT_PUBLISH_TOPIC', default='/gps/nmea'))

    setup_logging(log_level)
    logger = logging.getLogger(client_name)
    atexit.register(on_exit)

    client = SimpleMqttClient.SimpleMqttClient(broker, port, 60, client_name, client_name)
    if not client.connect():
        exit()

    stream = Serial(serial_device, 9600, timeout=3)
    with stream:
        while(run):
            nmr = NMEAReader(stream)
            (raw_data, parsed_data) = nmr.read()
            logger.debug(parsed_data)
            client.publish(publish_topic, raw_data)     
