import roles
from PyQt5.QtCore import Qt, QObject, QAbstractListModel, QModelIndex, pyqtProperty, pyqtSignal, pyqtSlot, QVariant
import logging

logger = logging.getLogger("logger")


class SatellitesModel(QAbstractListModel):
    countChanged = pyqtSignal()

    SvIdRole = roles.getNextRoleId()
    CnoRole = roles.getNextRoleId()
    IsUsedRole = roles.getNextRoleId()
    ElevationRole = roles.getNextRoleId()
    AzimuthRole = roles.getNextRoleId()
    PrnRole = roles.getNextRoleId()

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
        }

    @pyqtProperty(int, notify=countChanged)
    def usedCount(self):
        return sum(map(lambda sat: sat["used"], self._satellites))

    @pyqtProperty(int, notify=countChanged)
    def knownPosCount(self):
        return sum(map(lambda sat: sat["elevation"] is not None and sat["azimuth"] is not None, self._satellites))

    @pyqtSlot(QVariant)
    def addSatellite(self, sat):
        logger.debug("add satellite {}".format(sat["svid"]))
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

        if len(changedRoles) > 0:
            logger.debug("update satellite {}".format(sat["svid"]))
        self.dataChanged.emit(ix, ix, changedRoles)
        self.countChanged.emit()

    @pyqtSlot(int)
    def removeSatellite(self, svid):
        logger.debug("remove satellite {}".format(svid))
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

