import logging as log
import atexit
import os
import uuid
import time
import sysinfo
import threading
from copy import deepcopy
import shutil
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


def runPeriodicPublish(messenger, publishTopic, wifiManager):
    intervalSeconds = 1
    while True:
        system = dict()
        system["wifi"] = wifiManager.wifi
        system["wifilist"] = list(wifiManager.wifiEntries.values())
        system["resources"] = sysinfo.Resources.parseMemInfo(sysinfo.Resources.getMemInfoFromProcfs())
        system["resources"]["cpuTemp"] = sysinfo.Resources.parseCpuTemperature(sysinfo.Resources.getCpuTempFromSysfs())
        system["resources"]["cpuUsage"] = sysinfo.Resources.parseCpuUsage(sysinfo.Resources.getStatFromProcfs())
        messenger.sendNotification(publishTopic, json.dumps(system))
        time.sleep(intervalSeconds)


class WifiEntry(dict):
    KNOWN = "known"
    ADDED = "added"
    REMOVED = "removed"
    NEW = "new"

    def __init__(self, ssid, state, isConnected, frequency, accesspoint, linkQuality, signalLevel, isEncrypted, psk=None):
        self["ssid"] = ssid
        self["state"] = state
        self["isConnected"] = isConnected
        self["frequency"] = frequency
        self["accesspoint"] = accesspoint
        self["linkQuality"] = linkQuality
        self["signalLevel"] = signalLevel
        self["isEncrypted"] = isEncrypted
        self._psk = psk


class WifiManager:

    def __init__(self, iface):
        self._iface = iface
        self._wifi = dict()
        self._wpaSupplicantConf = sysinfo.Wifi.parseWpaSupplicantConf(sysinfo.Wifi.getWpaSupplicantConf())
        self._wifiEntries = dict()
        self._wifiEntriesLock = threading.Lock()
        log.info(repr(self._wpaSupplicantConf))
        self._updateWifiEntriesFromWpaSupplicantConfig()
        self._iwLock = threading.Lock()
        self._propertyLock = threading.Lock()
        self._timerWifiList = threading.Timer(0, self._getWifiList)
        self._timerWifiConfig = threading.Timer(0, self._getWifiConfig)

    @property
    def wifi(self):
        with self._propertyLock:
            return deepcopy(self._wifi)

    @property
    def wifiEntries(self):
        with self._wifiEntriesLock:
            return deepcopy(self._wifiEntries)

    def startScanning(self):
        with self._iwLock:
            self._timerWifiList.start()
            self._timerWifiConfig.start()

    def stopScanning(self):
        with self._iwLock:
            self._timerWifiList.cancel()
            self._timerWifiConfig.cancel()

    def addWifiNetwork(self, ssid, psk):
        if ssid in self._wifiEntries.keys():
            if self._wifiEntries[ssid]["state"] == WifiEntry.NEW:
                self._wifiEntries[ssid]._psk = psk
                self._wifiEntries[ssid]["state"] = WifiEntry.ADDED
            else:
                raise KeyError("network with ssid {} already exists".format(ssid))
        else:
            self._wifiEntries[ssid] = WifiEntry(ssid, WifiEntry.ADDED, False, None, None, None, None, None, psk)

    def removeWifiNetwork(self, ssid):
        if ssid in self._wifiEntries.keys():
            if self._wifiEntries[ssid]["state"] == WifiEntry.KNOWN:
                self._wifiEntries[ssid]["state"] = WifiEntry.REMOVED
            else:
                raise KeyError("cannot remove wifi network {} in state {}".format(ssid, self._wifiEntries[ssid]["state"]))
        else:
            raise KeyError("ssid {} not found".format(ssid))

    def saveChanges(self, targetFile="/etc/wpa_supplicant/wpa_supplicant.conf"):
        with self._wifiEntriesLock:
            for entry in self._wifiEntries.values():
                if entry["state"] == WifiEntry.ADDED:
                    log.info("add {}, {}".format(entry["ssid"], entry._psk))
                    self._wpaSupplicantConf["networks"].append({"ssid": entry["ssid"], "psk": entry._psk})
                elif entry["state"] == WifiEntry.REMOVED:
                    for index, network in enumerate(list(self._wpaSupplicantConf["networks"])):
                        if network["ssid"] == entry["ssid"]:
                            del self._wpaSupplicantConf["networks"][index]
        backupFile = targetFile + ".bkp"
        shutil.copy(targetFile, backupFile)
        with open(targetFile, "w") as f:
            f.write(sysinfo.Wifi.wpaSupplicantConfToStr(self._wpaSupplicantConf))
            self._updateWifiEntriesFromWpaSupplicantConfig()
        self.forceReconnect()

    def forceReconnect(self):
        # enforce wifi reconnection by restarting dhcpcd
        sysinfo.restartDhcpcd()

    def _updateWifiEntriesFromWpaSupplicantConfig(self):
        with self._wifiEntriesLock:
            wpaSupplicantConfSSids = [net["ssid"] for net in self._wpaSupplicantConf["networks"]]
            for entry in self._wifiEntries.values():
                if entry["ssid"] in wpaSupplicantConfSSids:
                    entry["state"] = WifiEntry.KNOWN
                else:
                    entry["state"] = WifiEntry.NEW
            for ssid in wpaSupplicantConfSSids:
                if ssid not in self._wifiEntries.keys():
                    self._wifiEntries[ssid] = WifiEntry(ssid, WifiEntry.KNOWN, False, None, None, None, None, None)

    def _updateWifiEntriesIwListResult(self, wifilist):
        with self._wifiEntriesLock:
            for wifi in wifilist:
                # update existing wifi
                if wifi["ssid"] in self._wifiEntries.keys():
                    entry = self._wifiEntries[wifi["ssid"]]
                    entry["accesspoint"] = wifi["accesspoint"]
                    entry["frequency"] = wifi["frequency"]
                    entry["linkQuality"] = wifi["linkQuality"]
                    entry["signalLevel"] = wifi["signalLevel"]
                    entry["isEncrypted"] = wifi["encrypted"]
                    log.debug("updated {}".format(wifi["ssid"]))
                # add new wifi
                else:
                    self._wifiEntries[wifi["ssid"]] = WifiEntry(
                        wifi["ssid"],
                        WifiEntry.NEW,
                        False,
                        wifi["frequency"],
                        wifi["accesspoint"],
                        wifi["linkQuality"],
                        wifi["signalLevel"],
                        wifi["encrypted"]
                        )
                    log.debug("added {}".format(wifi["ssid"]))
            # remove wifis which are not anymore in scan result and are new to configuration
            scannedSsids = [w["ssid"] for w in wifilist]
            for k in list(self._wifiEntries.keys()):
                entry = self._wifiEntries[k]
                if entry["state"] == WifiEntry.NEW and not entry["ssid"] in scannedSsids:
                    del self._wifiEntries[k]
                elif not entry["ssid"] in scannedSsids:
                    entry["isConnected"] = False
                    entry["frequency"] = None
                    entry["accesspoint"] = None
                    entry["linkQuality"] = None
                    entry["signalLevel"] = None

    def _updateWifiEntriesFromIwConfigResult(self, connectedWifi):
        with self._wifiEntriesLock:
            if connectedWifi["ssid"] is None:
                for wifi in self._wifiEntries.values():
                    wifi["isConnected"] = False
            elif connectedWifi["ssid"] in self._wifiEntries.keys():
                wifi = self._wifiEntries[connectedWifi["ssid"]]
                wifi["isConnected"] = True
                wifi["frequency"] = connectedWifi["frequency"]
                wifi["accesspoint"] = connectedWifi["accesspoint"]
                wifi["linkQuality"] = connectedWifi["linkQuality"]
                wifi["signalLevel"] = connectedWifi["signalLevel"]
                log.debug("update connected wifi {}".format(connectedWifi["ssid"]))
            else:
                log.error("conntected to unkown wifi, this is not possible, {}".format(connectedWifi["ssid"]))

    def _getWifiList(self):
        with self._iwLock:
            self._timerWifiList = threading.Timer(10, self._getWifiList)
            self._timerWifiList.start()
            try:
                wifilist = sysinfo.Wifi.parseIwList(sysinfo.Wifi.getIwList(self._iface))
                self._updateWifiEntriesIwListResult(wifilist)
            except ChildProcessError as ex:
                log.error(str(ex))

    def _getWifiConfig(self):
        with self._iwLock:
            self._timerWifiConfig = threading.Timer(3, self._getWifiConfig)
            self._timerWifiConfig.start()
            wifi = sysinfo.Wifi.parseIwConfig(sysinfo.Wifi.getIwConfig(self._iface))
            self._updateWifiEntriesFromIwConfigResult(wifi)
            with self._propertyLock:
                self._wifi = wifi


class MessageHandler:

    def __init__(self, wifiManager):
        self._wifiManager = wifiManager

    def onMessage(self, msg):
        if "command" in msg.keys():
            if msg["command"] == "addWifi":
                self._wifiManager.addWifiNetwork(msg["data"]["ssid"], msg["data"]["psk"])
            if msg["command"] == "removeWifi":
                self._wifiManager.removeWifiNetwork(msg["data"]["ssid"])
            if msg["command"] == "saveChanges":
                self._wifiManager.saveChanges()
            if msg["command"] == "forceReconnect":
                self._wifiManager.forceReconnect()


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

    wifiManager = WifiManager(wifiIface)
    messageHandler = MessageHandler(wifiManager)
    mqClient = mqtt.launch(clientName, broker, port)
    subscriptions = {
        ctrlTopic: {
            "type": mqtt.MqttMessenger.REQUEST,
            "func": messageHandler.onMessage
        }
    }
    messenger = mqtt.MqttMessenger(mqClient, subscriptions)
    atexit.register(onExit, mqClient)

    wifiManager.startScanning()

    runPeriodicPublish(messenger, infoTopic, wifiManager)


if __name__ == "__main__":
    main()
