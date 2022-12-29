import bme280
import smbus2
import logging as log
import atexit
import os
import uuid
import time
import json

try:
    import common.mqtt as mqtt
    import common.util as util
except ImportError:
    import mqtt
    import util


def onExit(mqClient):
    log.info("Exit application")
    if mqClient is not None:
        mqClient.disconnect()


def calculatePressureAltitude(pressure, temperature) -> float:
    referencePressure = 1013.25  # hPa
    # hypsometric formula, should be accurate enough for altitudes up to 11km
    return (((referencePressure / pressure) ** (1 / 5.257) - 1) * (temperature + 273.15)) / 0.0065


def runPeriodicPublish(mqClient, bus, address, calibrationParams, publishTopic):
    intervalSeconds = 1
    while True:
        start = time.perf_counter()
        # x8 oversampling, 115ms, ~8.7Hz
        # x16 oversampling, 225ms, ~4 Hz
        data = bme280.sample(bus, address, calibrationParams, bme280.oversampling.x16)
        obj = dict()
        obj["humidity"] = round(data.humidity, 3)  # %H
        obj["pressure"] = round(data.pressure, 3)  # hPa
        obj["temperature"] = round(data.temperature, 3)  # °C
        obj["pressureAltitude"] = round(calculatePressureAltitude(data.pressure, data.temperature), 3)  # m
        js = json.dumps(obj)
        log.debug(js)
        mqClient.publish(publishTopic, js)
        end = time.perf_counter()
        usedSeconds = (end-start)
        sleepSeconds = intervalSeconds - usedSeconds
        if sleepSeconds < 0:
            log.warning("periodic function takes longer than requested interval of {} seconds".format(intervalSeconds))
            sleepSeconds = 0
        time.sleep(sleepSeconds)


def main():
    i2cPort = int(os.getenv("BM_I2C_PORT"))
    i2cAddress = int(os.getenv("BM_I2C_ADDRESS"), 16)
    logLevel = str(os.getenv("BM_LOG_LEVEL"))
    broker = str(os.getenv("BM_MQTT_HOST"))
    port = int(os.getenv("BM_MQTT_PORT"))
    clientName = str(os.getenv("BM_MQTT_CLIENT_NAME"))
    publishTopic = str(os.getenv("BM_MQTT_PUBLISH_TOPIC"))

    util.setupLogging(logLevel)

    if clientName == "":
        log.info("mqtt client name is empty, assign uuid")
        clientName = str(uuid.uuid1())

    mqClient = mqtt.launch(clientName, broker, port, [], None)
    atexit.register(onExit, mqClient)

    # BME280 sensor stuff
    bus = smbus2.SMBus(i2cPort)
    calibration_params = bme280.load_calibration_params(bus, i2cAddress)
    log.info("start publishing i2c messages to {topic}".format(topic=publishTopic))
    runPeriodicPublish(mqClient, bus, i2cAddress, calibration_params, publishTopic)


if __name__ == "__main__":
    main()
