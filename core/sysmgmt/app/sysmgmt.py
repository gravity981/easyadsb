import logging as log
import atexit
import os
import uuid
import time
import json
import sysinfo

try:
    import common.mqtt as mqtt
    import common.logconf as logconf
except ImportError:
    import mqtt
    import logconf


def onExit(mqClient):
    log.info("Exit application")
    if mqClient is not None:
        mqClient.disconnect()


def runPeriodicPublish(mqClient, publishTopic, wifiIface):
    intervalSeconds = 1
    while True:
        system = dict()
        system["wifi"] = sysinfo.Wifi.parseIwConfig(sysinfo.Wifi.getIwConfig(wifiIface))
        system["resources"] = sysinfo.Resources.parseMemInfo(sysinfo.Resources.getMemInfoFromProcfs())
        system["resources"]["cpuTemp"] = sysinfo.Resources.parseCpuTemperature(sysinfo.Resources.getCpuTempFromSysfs())
        system["resources"]["cpuUsage"] = sysinfo.Resources.parseCpuUsage(sysinfo.Resources.getStatFromProcfs())
        system = json.dumps(system)
        mqClient.publish("/easyadsb/sysmgmt/json", system)
        time.sleep(intervalSeconds)


def main():
    logLevel = str(os.getenv("SY_LOG_LEVEL"))
    broker = str(os.getenv("SY_MQTT_HOST"))
    port = int(os.getenv("SY_MQTT_PORT"))
    clientName = str(os.getenv("SY_MQTT_CLIENT_NAME"))
    publishTopic = str(os.getenv("SY_MQTT_PUBLISH_TOPIC"))
    wifiIface = str(os.getenv("SY_WIFI_IFACE"))

    logconf.setupLogging(logLevel)

    if clientName == "":
        log.info("mqtt client name is empty, assign uuid")
        clientName = str(uuid.uuid1())

    mqClient = mqtt.launch(clientName, broker, port, [], None)
    atexit.register(onExit, mqClient)

    runPeriodicPublish(mqClient, publishTopic, wifiIface)


if __name__ == "__main__":
    main()
