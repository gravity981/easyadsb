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
    import common.util as util
except ImportError:
    import mqtt
    import util


def onExit(mqClient):
    log.info("Exit application")
    if mqClient is not None:
        mqClient.disconnect()


def runPeriodicPublish(mqClient, publishTopic, wifiManager):
    intervalSeconds = 1
    while True:
        system = dict()
        system["wifi"] = wifiManager.wifi
        system["wifilist"] = wifiManager.wifilist
        system["resources"] = sysinfo.Resources.parseMemInfo(sysinfo.Resources.getMemInfoFromProcfs())
        system["resources"]["cpuTemp"] = sysinfo.Resources.parseCpuTemperature(sysinfo.Resources.getCpuTempFromSysfs())
        system["resources"]["cpuUsage"] = sysinfo.Resources.parseCpuUsage(sysinfo.Resources.getStatFromProcfs())
        system = json.dumps(system)
        mqClient.publish(publishTopic, system)
        time.sleep(intervalSeconds)


class WifiManager:

    def __init__(self, iface):
        self._iface = iface
        self._wifilist = []
        self._wifi = dict()
        self._wpaSupplicantConf = sysinfo.Wifi.parseWpaSupplicantConf(sysinfo.Wifi.getWpaSupplicantConf())
        self._iwLock = threading.Lock()
        self._propertyLock = threading.Lock()
        self._timerWifiList = threading.Timer(0, self._getWifiList)
        self._timerWifiConfig = threading.Timer(0, self._getWifiConfig)

    @property
    def wifilist(self):
        with self._propertyLock:
            return deepcopy(self._wifilist)

    @property
    def wifi(self):
        with self._propertyLock:
            return deepcopy(self._wifi)

    def startScanning(self):
        with self._iwLock:
            self._timerWifiList.start()
            self._timerWifiConfig.start()

    def stopScanning(self):
        with self._iwLock:
            self._timerWifiList.cancel()
            self._timerWifiConfig.cancel()

    def _getWifiList(self):
        with self._iwLock:
            self._timerWifiList = threading.Timer(10, self._getWifiList)
            self._timerWifiList.start()
            wifilist = sysinfo.Wifi.parseIwList(sysinfo.Wifi.getIwList(self._iface))
            with self._propertyLock:
                self._wifilist = wifilist

    def _getWifiConfig(self):
        with self._iwLock:
            self._timerWifiConfig = threading.Timer(3, self._getWifiConfig)
            self._timerWifiConfig.start()
            wifi = sysinfo.Wifi.parseIwConfig(sysinfo.Wifi.getIwConfig(self._iface))
            with self._propertyLock:
                self._wifi = wifi


def main():
    logLevel = str(os.getenv("SY_LOG_LEVEL"))
    broker = str(os.getenv("SY_MQTT_HOST"))
    port = int(os.getenv("SY_MQTT_PORT"))
    clientName = str(os.getenv("SY_MQTT_CLIENT_NAME"))
    publishTopic = str(os.getenv("SY_MQTT_PUBLISH_TOPIC"))
    wifiIface = str(os.getenv("SY_WIFI_IFACE"))

    util.setupLogging(logLevel)

    if clientName == "":
        log.info("mqtt client name is empty, assign uuid")
        clientName = str(uuid.uuid1())

    mqClient = mqtt.launch(clientName, broker, port, [], None)
    atexit.register(onExit, mqClient)

    wifiManager = WifiManager(wifiIface)
    wifiManager.startScanning()

    runPeriodicPublish(mqClient, publishTopic, wifiManager)


if __name__ == "__main__":
    main()
