import roles
from PyQt5.QtCore import Qt, QObject, QAbstractListModel, QModelIndex, pyqtProperty, pyqtSignal, pyqtSlot, QVariant
import logging as log


class SatellitesModel(QAbstractListModel):
    countChanged = pyqtSignal()

    SvIdRole = roles.getNextRoleId()
    CnoRole = roles.getNextRoleId()
    IsUsedRole = roles.getNextRoleId()
    ElevationRole = roles.getNextRoleId()
    AzimuthRole = roles.getNextRoleId()
    PrnRole = roles.getNextRoleId()
    MaxCno = roles.getNextRoleId()

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self._satellites = []

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        if role == SatellitesModel.SvIdRole:
            return self._satellites[row]["svid"]
        if role == SatellitesModel.CnoRole:
            return self._satellites[row]["cno"]
        if role == SatellitesModel.IsUsedRole:
            return self._satellites[row]["used"]
        if role == SatellitesModel.ElevationRole:
            return self._satellites[row]["elevation"]
        if role == SatellitesModel.AzimuthRole:
            return self._satellites[row]["azimuth"]
        if role == SatellitesModel.PrnRole:
            return self._satellites[row]["prn"]
        if role == SatellitesModel.MaxCno:
            return self._satellites[row]["maxCno"]

    def rowCount(self, parent=QModelIndex()):
        return len(self._satellites)

    def roleNames(self):
        return {
            SatellitesModel.SvIdRole: b"svid",
            SatellitesModel.CnoRole: b"cno",
            SatellitesModel.IsUsedRole: b"isUsed",
            SatellitesModel.ElevationRole: b"elv",
            SatellitesModel.AzimuthRole: b"az",
            SatellitesModel.PrnRole: b"prn",
            SatellitesModel.MaxCno: b"maxCno",
        }

    @pyqtProperty(int, notify=countChanged)
    def usedCount(self):
        return sum(map(lambda sat: sat["used"], self._satellites))

    @pyqtProperty(int, notify=countChanged)
    def knownPosCount(self):
        return sum(map(lambda sat: sat["elevation"] is not None and sat["azimuth"] is not None, self._satellites))

    @pyqtProperty(int, notify=countChanged)
    def maxCnoTotal(self):
        minCnoTotal = 60
        maxCno = None
        if len(self._satellites) > 0:
            maxCno = max(self._satellites, key=lambda x: (x["maxCno"] if x["maxCno"] is not None else 0))["maxCno"]
        if maxCno is None:
            return minCnoTotal
        return max(maxCno, minCnoTotal)

    @pyqtSlot(QVariant)
    def addSatellite(self, sat):
        log.debug("add satellite {}".format(sat["svid"]))
        sat["maxCno"] = sat["cno"]
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._satellites.append(sat)
        self.endInsertRows()

    @pyqtSlot(QVariant)
    def updateSatellite(self, sat):
        row = self._rowFromSvId(sat["svid"])
        ix = self.index(row, 0)
        changedRoles = []
        if self._satellites[row]["svid"] != sat["svid"]:
            self._satellites[row]["svid"] = sat["svid"]
            changedRoles.append(SatellitesModel.SvIdRole)
        if self._satellites[row]["elevation"] != sat["elevation"]:
            self._satellites[row]["elevation"] = sat["elevation"]
            changedRoles.append(SatellitesModel.ElevationRole)
        if self._satellites[row]["azimuth"] != sat["azimuth"]:
            self._satellites[row]["azimuth"] = sat["azimuth"]
            changedRoles.append(SatellitesModel.AzimuthRole)
        if self._satellites[row]["cno"] != sat["cno"]:
            self._satellites[row]["cno"] = sat["cno"]
            changedRoles.append(SatellitesModel.CnoRole)
        if self._satellites[row]["used"] != sat["used"]:
            self._satellites[row]["used"] = sat["used"]
            changedRoles.append(SatellitesModel.IsUsedRole)
        if self._satellites[row]["prn"] != sat["prn"]:
            self._satellites[row]["prn"] = sat["prn"]
            changedRoles.append(SatellitesModel.PrnRole)

        oldMaxCno = self._satellites[row]["maxCno"]
        if sat["cno"] is not None:
            if oldMaxCno is not None:
                self._satellites[row]["maxCno"] = max(sat["cno"], oldMaxCno)
            else:
                self._satellites[row]["maxCno"] = sat["cno"]
        if oldMaxCno != self._satellites[row]["maxCno"]:
            changedRoles.append(SatellitesModel.MaxCno)

        if len(changedRoles) > 0:
            log.debug("update satellite {}".format(sat["svid"]))
        self.dataChanged.emit(ix, ix, changedRoles)
        self.countChanged.emit()

    @pyqtSlot(int)
    def removeSatellite(self, svid):
        log.debug("remove satellite {}".format(svid))
        row = self._rowFromSvId(svid)
        self.beginRemoveRows(QModelIndex(), row, row)
        del self._satellites[row]
        self.endRemoveRows()

    @property
    def svids(self) -> list():
        return [s["svid"] for s in self._satellites]

    def _rowFromSvId(self, svid):
        for index, item in enumerate(self._satellites):
            if item["svid"] == svid:
                return index
        raise ValueError("no satellite for svid {}".format(svid))
