import logging as log
import atexit
import os
import uuid
import time
import json
import sysinfo
import threading
from copy import deepcopy
import shutil

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


def runPeriodicPublish(messageDispatcher, publishTopic, wifiManager):
    intervalSeconds = 1
    while True:
        system = dict()
        system["wifi"] = wifiManager.wifi
        system["wifilist"] = wifiManager.wifilist
        system["resources"] = sysinfo.Resources.parseMemInfo(sysinfo.Resources.getMemInfoFromProcfs())
        system["resources"]["cpuTemp"] = sysinfo.Resources.parseCpuTemperature(sysinfo.Resources.getCpuTempFromSysfs())
        system["resources"]["cpuUsage"] = sysinfo.Resources.parseCpuUsage(sysinfo.Resources.getStatFromProcfs())
        messageDispatcher.sendNotification(publishTopic, system)
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

    def addWifiNetwork(self, ssid, psk):
        self._wpaSupplicantConf["networks"].append(
            {
                "ssid": ssid,
                "psk": psk
            }
        )

    def removeWifiNetwork(self, ssid):
        removed = False
        for index, network in enumerate(list(self._wpaSupplicantConf["networks"])):
            if ssid in network["ssid"]:
                del self._wpaSupplicantConf["networks"][index]
                removed = True
        if not removed:
            raise KeyError("ssid {} not found".format(ssid))

    def saveChanges(self, targetFile="/etc/wpa_supplicant/wpa_supplicant.conf"):
        backupFile = targetFile + ".bkp"
        shutil.copy(targetFile, backupFile)
        with open(targetFile, "w") as f:
            f.write(sysinfo.Wifi.wpaSupplicantConfToStr(self._wpaSupplicantConf))
        self.forceReconnect()

    def forceReconnect(self):
        # todo restart dhcpcd systemd service in order to make it connect to any configured wifi in range
        # this should not be necessary but the system does not always work reliable
        log.warning("force reconnect not yet implemented")

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


class MessageHandler:

    def __init__(self, wifiManager):
        self._wifiManager = wifiManager

    def onMessage(self, msg):
        log.info(msg)


def main():
    logLevel = str(os.getenv("SY_LOG_LEVEL"))
    broker = str(os.getenv("SY_MQTT_HOST"))
    port = int(os.getenv("SY_MQTT_PORT"))
    clientName = str(os.getenv("SY_MQTT_CLIENT_NAME"))
    infoTopic = str(os.getenv("SY_MQTT_INFO_TOPIC"))
    ctrlTopic = str(os.getenv("SY_MQTT_CTRL_TOPIC"))
    wifiIface = str(os.getenv("SY_WIFI_IFACE"))

    util.setupLogging(logLevel)

    if clientName == "":
        log.info("mqtt client name is empty, assign uuid")
        clientName = str(uuid.uuid1())

    mqClient = mqtt.launch(clientName, broker, port, [], None)
    wifiManager = WifiManager(wifiIface)
    messageHandler = MessageHandler(wifiManager)
    subscriptions = {
        ctrlTopic + "/request": {
            "type": mqtt.MessageDispatcher.REQUEST,
            "func": messageHandler.onMessage
        }
    }
    messageDispatcher = mqtt.MessageDispatcher(mqClient, subscriptions)
    atexit.register(onExit, mqClient)

    wifiManager.startScanning()

    runPeriodicPublish(messageDispatcher, infoTopic, wifiManager)


if __name__ == "__main__":
    main()
