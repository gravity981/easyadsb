import logging as log
import atexit
import os
import uuid
import time
import json
import sysinfo
import threading
from copy import deepcopy

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

def runPeriodicPublish(mqClient, publishTopic, iface, wifiscanner):
    intervalSeconds = 1
    while True:
        system = dict()
        system["wifi"] = sysinfo.Wifi.parseIwConfig(sysinfo.Wifi.getIwConfig(iface))
        system["wifilist"] = wifiscanner.wifilist
        system["resources"] = sysinfo.Resources.parseMemInfo(sysinfo.Resources.getMemInfoFromProcfs())
        system["resources"]["cpuTemp"] = sysinfo.Resources.parseCpuTemperature(sysinfo.Resources.getCpuTempFromSysfs())
        system["resources"]["cpuUsage"] = sysinfo.Resources.parseCpuUsage(sysinfo.Resources.getStatFromProcfs())
        system = json.dumps(system)
        mqClient.publish("/easyadsb/sysmgmt/json", system)
        time.sleep(intervalSeconds)


class WifiScanner:

    def __init__(self, iface):
        self._iface = iface
        self._wifilist = []
        self._lock = threading.Lock()
        self._timer = threading.Timer(0, self._scanWifi)

    @property
    def wifilist(self):
        with self._lock:
            return deepcopy(self._wifilist)

    def start(self):
        with self._lock:
            self._timer.start()

    def stop(self):
        with self._lock:
            self._timer.stop()

    def _scanWifi(self):
        with self._lock:
            self._timer = threading.Timer(10, self._scanWifi)
            self._timer.start()
            self._wifilist = sysinfo.Wifi.parseIwList(sysinfo.Wifi.getIwList(self._iface))


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

    wifiscanner = WifiScanner(wifiIface)
    wifiscanner.start()

    runPeriodicPublish(mqClient, publishTopic, wifiIface, wifiscanner)


if __name__ == "__main__":
    main()
