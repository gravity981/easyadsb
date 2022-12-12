import bme280
import smbus2
import logging
import atexit
import os
import uuid
import time
import json

try:
    import common.mqtt as mqtt
    import common.logconf as logconf
except ImportError:
    import mqtt
    import logconf


def on_exit():
    if logger is not None:
        logger.info("Exit application")
    if mqClient is not None:
        mqClient.disconnect()


def calculatePressureAltitude(pressure, temperature) -> float:
    referencePressure = 1013.25  # hPa
    # hypsometric formula, should work for altitudes up to 11km
    return (((referencePressure / pressure) ** (1 / 5.257) - 1) * (temperature + 273.15)) / 0.0065


def run_periodic_publish(mqClient, bus, address):
    while True:
        data = bme280.sample(bus, address, calibration_params)
        obj = dict()
        obj["humidity"] = round(data.humidity, 3)  # %H
        obj["pressure"] = round(data.pressure, 3)  # hPa
        obj["temperature"] = round(data.temperature, 3)  # °C
        obj["pressureAltitude"] = round(calculatePressureAltitude(data.pressure, data.temperature), 3)  # m
        js = json.dumps(obj)
        logger.debug(js)
        mqClient.publish(publish_topic, js)
        time.sleep(1)


if __name__ == "__main__":
    logger = None
    mqClient = None
    run = True

    logger_name = "logger"
    i2c_port = int(os.getenv("BM_I2C_PORT"))
    i2c_address = int(os.getenv("BM_I2C_ADDRESS"), 16)
    log_level = str(os.getenv("BM_LOG_LEVEL"))
    broker = str(os.getenv("BM_MQTT_HOST"))
    port = int(os.getenv("BM_MQTT_PORT"))
    client_name = str(os.getenv("BM_MQTT_CLIENT_NAME"))
    publish_topic = str(os.getenv("BM_MQTT_PUBLISH_TOPIC"))

    logconf.setup_logging(log_level)
    logger = logging.getLogger(logger_name)
    atexit.register(on_exit)

    if client_name == "":
        logger.info("client_name is empty, assign uuid")
        client_name = str(uuid.uuid1())

    mqClient = mqtt.launch(client_name, broker, port)

    # BME280 sensor stuff
    bus = smbus2.SMBus(i2c_port)
    calibration_params = bme280.load_calibration_params(bus, i2c_address)
    logger.info("start publishing i2c messages to {topic}".format(topic=publish_topic))
    run_periodic_publish(mqClient, bus, i2c_address)
