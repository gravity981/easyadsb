import roles
from PyQt5.QtCore import Qt, QObject, QAbstractListModel, QModelIndex, pyqtSlot, QVariant
import logging as log
import sys

try:
    try:
        import common.mqtt as mqtt
        import common.util as util
    except ImportError:
        import mqtt
        import util
except ImportError:
    sys.path.insert(0, '../../common')
    import mqtt
    import util


class WifiSettingsModel(QAbstractListModel):
    SsidRole = roles.getNextRoleId()
    IsKnownRole = roles.getNextRoleId()
    isConnectedRole = roles.getNextRoleId()
    FrequencyRole = roles.getNextRoleId()
    AccesspointRole = roles.getNextRoleId()
    LinkQualityRole = roles.getNextRoleId()
    SignalLevelRole = roles.getNextRoleId()
    IsEncryptedRole = roles.getNextRoleId()

    def __init__(self, messenger, parent=None):
        QObject.__init__(self, parent)
        self._wifis = []
        self._messenger = messenger

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        if role == WifiSettingsModel.SsidRole:
            return self._wifis[row]["ssid"]
        if role == WifiSettingsModel.IsKnownRole:
            return self._wifis[row]["isKnown"]
        if role == WifiSettingsModel.isConnectedRole:
            return self._wifis[row]["isConnected"]
        if role == WifiSettingsModel.FrequencyRole:
            return self._wifis[row]["frequency"]
        if role == WifiSettingsModel.AccesspointRole:
            return self._wifis[row]["accesspoint"]
        if role == WifiSettingsModel.LinkQualityRole:
            return self._wifis[row]["linkQuality"]
        if role == WifiSettingsModel.SignalLevelRole:
            return self._wifis[row]["signalLevel"]
        if role == WifiSettingsModel.IsEncryptedRole:
            return self._wifis[row]["isEncrypted"]

    def rowCount(self, parent=QModelIndex()):
        return len(self._wifis)

    def roleNames(self):
        return {
            WifiSettingsModel.SsidRole: b"ssid",
            WifiSettingsModel.IsKnownRole: b"isKnown",
            WifiSettingsModel.isConnectedRole: b"isConnected",
            WifiSettingsModel.FrequencyRole: b"frequency",
            WifiSettingsModel.AccesspointRole: b"accesspoint",
            WifiSettingsModel.LinkQualityRole: b"linkQuality",
            WifiSettingsModel.SignalLevelRole: b"signalLevel",
            WifiSettingsModel.IsEncryptedRole: b"isEncrypted",
        }

    @property
    def ssids(self) -> list():
        return [w["ssid"] for w in self._wifis]

    @pyqtSlot(QVariant)
    def onWifiListUpdated(self, wifilist):
        oldSsids = self.ssids
        wifilist = wifilist["wifilist"]
        for wifi in wifilist:
            if wifi["ssid"] in oldSsids:
                self._updateWifi(wifi)
            else:
                self._addWifi(wifi)
        ssids = [s["ssid"] for s in wifilist]
        for oldSsid in oldSsids:
            if oldSsid not in ssids:
                self._removeWifi(oldSsid)

    @pyqtSlot(str, str)
    def addWifi(self, ssid, psk):
        request = mqtt.RequestMessage("addWifi", {"ssid": ssid, "psk": util.wpaPsk(ssid, psk).decode("utf-8")})
        response = self._messenger.sendRequestAndWait(self._sysCtrlTopic, request)
        return response["success"]

    def _updateWifi(self, wifi):
        row = self._rowFromSsid(wifi["ssid"])
        ix = self.index(row, 0)
        changedRoles = []
        if self._wifis[row]["ssid"] != wifi["ssid"]:
            self._wifis[row]["ssid"] = wifi["ssid"]
            changedRoles.append(WifiSettingsModel.SsidRole)
        if self._wifis[row]["isKnown"] != wifi["isKnown"]:
            self._wifis[row]["isKnown"] = wifi["isKnown"]
            changedRoles.append(WifiSettingsModel.IsKnownRole)
        if self._wifis[row]["isConnected"] != wifi["isConnected"]:
            self._wifis[row]["isConnected"] = wifi["isConnected"]
            changedRoles.append(WifiSettingsModel.isConnectedRole)
        if self._wifis[row]["frequency"] != wifi["frequency"]:
            self._wifis[row]["frequency"] = wifi["frequency"]
            changedRoles.append(WifiSettingsModel.FrequencyRole)
        if self._wifis[row]["accesspoint"] != wifi["accesspoint"]:
            self._wifis[row]["accesspoint"] = wifi["accesspoint"]
            changedRoles.append(WifiSettingsModel.AccesspointRole)
        if self._wifis[row]["linkQuality"] != wifi["linkQuality"]:
            self._wifis[row]["linkQuality"] = wifi["linkQuality"]
            changedRoles.append(WifiSettingsModel.LinkQualityRole)
        if self._wifis[row]["signalLevel"] != wifi["signalLevel"]:
            self._wifis[row]["signalLevel"] = wifi["signalLevel"]
            changedRoles.append(WifiSettingsModel.SignalLevelRole)
        if self._wifis[row]["isEncrypted"] != wifi["isEncrypted"]:
            self._wifis[row]["isEncrypted"] = wifi["isEncrypted"]
            changedRoles.append(WifiSettingsModel.IsEncryptedRole)

        self.dataChanged.emit(ix, ix, changedRoles)

    def _addWifi(self, wifi):
        log.debug("add wifi {}".format(wifi["ssid"]))
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._wifis.append(wifi)
        self.endInsertRows()

    def _removeWifi(self, ssid):
        log.debug("remove wifi {}".format(ssid))
        row = self._rowFromSsid(ssid)
        self.beginRemoveRows(QModelIndex(), row, row)
        del self._wifis[row]
        self.endRemoveRows()

    def _rowFromSsid(self, ssid):
        for index, item in enumerate(self._wifis):
            if item["ssid"] == ssid:
                return index
        raise ValueError("no wifi for ssid {}".format(ssid))
