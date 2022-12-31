import roles
from PyQt5.QtCore import Qt, QObject, QAbstractListModel, QModelIndex, pyqtSlot, QVariant
import logging as log


class WifiSettingsModel(QAbstractListModel):
    SsidRole = roles.getNextRoleId()
    IsKnownRole = roles.getNextRoleId()
    isConnectedRole = roles.getNextRoleId()
    FrequencyRole = roles.getNextRoleId()
    AccesspointRole = roles.getNextRoleId()
    LinkQualityRole = roles.getNextRoleId()
    SignalLevelRole = roles.getNextRoleId()
    IsEncryptedRole = roles.getNextRoleId()

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self._wifis = []

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

    @pyqtSlot(QVariant)
    def onWifiListUpdated(wifilist):
        log.info("wifilist updated")
