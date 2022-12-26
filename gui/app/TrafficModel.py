import roles
from PyQt5.QtCore import Qt, QObject, QAbstractListModel, QModelIndex, pyqtSlot, QVariant
import logging
import os

logger = logging.getLogger("logger")


class TrafficModel(QAbstractListModel):
    IdRole = roles.getNextRoleId()
    CallsignRole = roles.getNextRoleId()
    TypeRole = roles.getNextRoleId()
    CategoryRole = roles.getNextRoleId()
    LatitudeRole = roles.getNextRoleId()
    LongitudeRole = roles.getNextRoleId()
    AltitudeRole = roles.getNextRoleId()
    TrackRole = roles.getNextRoleId()
    GroundSpeedRole = roles.getNextRoleId()
    VerticalSpeedRole = roles.getNextRoleId()
    SquawkRole = roles.getNextRoleId()
    AlertRole = roles.getNextRoleId()
    EmergencyRole = roles.getNextRoleId()
    SpiRole = roles.getNextRoleId()
    IsOnGroundRole = roles.getNextRoleId()
    LastSeenRole = roles.getNextRoleId()
    MsgCountRole = roles.getNextRoleId()
    ImageSourcePathRole = roles.getNextRoleId()

    def __init__(self, aircraftImagesPath, parent=None):
        QObject.__init__(self, parent)
        self._trafficEntries = []
        self._aircraftImagesPath = aircraftImagesPath

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        if role == TrafficModel.IdRole:
            return self._trafficEntries[row]["id"]
        if role == TrafficModel.CallsignRole:
            return self._trafficEntries[row]["callsign"]
        if role == TrafficModel.TypeRole:
            return self._trafficEntries[row]["model"]
        if role == TrafficModel.CategoryRole:
            return self._trafficEntries[row]["category"]
        if role == TrafficModel.LatitudeRole:
            return self._trafficEntries[row]["latitude"]
        if role == TrafficModel.LongitudeRole:
            return self._trafficEntries[row]["longitude"]
        if role == TrafficModel.AltitudeRole:
            return self._trafficEntries[row]["altitude"]
        if role == TrafficModel.TrackRole:
            return self._trafficEntries[row]["track"]
        if role == TrafficModel.GroundSpeedRole:
            return self._trafficEntries[row]["groundSpeed"]
        if role == TrafficModel.VerticalSpeedRole:
            return self._trafficEntries[row]["verticalSpeed"]
        if role == TrafficModel.SquawkRole:
            return self._trafficEntries[row]["squawk"]
        if role == TrafficModel.AlertRole:
            return self._trafficEntries[row]["alert"]
        if role == TrafficModel.EmergencyRole:
            return self._trafficEntries[row]["emergency"]
        if role == TrafficModel.SpiRole:
            return self._trafficEntries[row]["spi"]
        if role == TrafficModel.IsOnGroundRole:
            return self._trafficEntries[row]["isOnGround"]
        if role == TrafficModel.LastSeenRole:
            return self._trafficEntries[row]["lastSeen"]
        if role == TrafficModel.MsgCountRole:
            return self._trafficEntries[row]["msgCount"]
        if role == TrafficModel.ImageSourcePathRole:
            return self._trafficEntries[row]["imageSourcePath"]

    def rowCount(self, parent=QModelIndex()):
        return len(self._trafficEntries)

    def roleNames(self):
        return {
            TrafficModel.IdRole: b"id",
            TrafficModel.CallsignRole: b"callsign",
            TrafficModel.TypeRole: b"type",
            TrafficModel.CategoryRole: b"category",
            TrafficModel.LatitudeRole: b"latitude",
            TrafficModel.LongitudeRole: b"longitude",
            TrafficModel.AltitudeRole: b"altitude",
            TrafficModel.TrackRole: b"track",
            TrafficModel.GroundSpeedRole: b"groundSpeed",
            TrafficModel.VerticalSpeedRole: b"verticalSpeed",
            TrafficModel.SquawkRole: b"squawk",
            TrafficModel.AlertRole: b"alert",
            TrafficModel.EmergencyRole: b"emergency",
            TrafficModel.SpiRole: b"spi",
            TrafficModel.IsOnGroundRole: b"isOnGround",
            TrafficModel.LastSeenRole: b"lastSeen",
            TrafficModel.MsgCountRole: b"msgCount",
            TrafficModel.ImageSourcePathRole: b"imageSourcePath",
        }

    @pyqtSlot(QVariant)
    def addTrafficEntry(self, entry):
        logger.debug("add traffic entry")
        entry["category"] = self._getCategoryName(entry["category"])
        entry["imageSourcePath"] = self._getImageSourcePath(entry["model"])
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._trafficEntries.append(entry)
        self.endInsertRows()

    @pyqtSlot(QVariant)
    def updateTrafficEntry(self, entry):
        row = self._rowFromId(entry["id"])
        ix = self.index(row, 0)
        changedRoles = []
        category = self._getCategoryName(entry["category"])
        if self._trafficEntries[row]["model"] != entry["model"]:
            self._trafficEntries[row]["imageSourcePath"] = self._getImageSourcePath(entry["model"])
            changedRoles.append(TrafficModel.ImageSourcePathRole)
        if self._trafficEntries[row]["id"] != entry["id"]:
            self._trafficEntries[row]["id"] = entry["id"]
            changedRoles.append(TrafficModel.IdRole)
        if self._trafficEntries[row]["callsign"] != entry["callsign"]:
            self._trafficEntries[row]["callsign"] = entry["callsign"]
            changedRoles.append(TrafficModel.CallsignRole)
        if self._trafficEntries[row]["model"] != entry["model"]:
            self._trafficEntries[row]["model"] = entry["model"]
            changedRoles.append(TrafficModel.ModelRole)
        if self._trafficEntries[row]["category"] != category:
            self._trafficEntries[row]["category"] = category
            changedRoles.append(TrafficModel.CategoryRole)
        if self._trafficEntries[row]["latitude"] != entry["latitude"]:
            self._trafficEntries[row]["latitude"] = entry["latitude"]
            changedRoles.append(TrafficModel.LatitudeRole)
        if self._trafficEntries[row]["longitude"] != entry["longitude"]:
            self._trafficEntries[row]["longitude"] = entry["longitude"]
            changedRoles.append(TrafficModel.LongitudeRole)
        if self._trafficEntries[row]["altitude"] != entry["altitude"]:
            self._trafficEntries[row]["altitude"] = entry["altitude"]
            changedRoles.append(TrafficModel.AltitudeRole)
        if self._trafficEntries[row]["track"] != entry["track"]:
            self._trafficEntries[row]["track"] = entry["track"]
            changedRoles.append(TrafficModel.TrackRole)
        if self._trafficEntries[row]["groundSpeed"] != entry["groundSpeed"]:
            self._trafficEntries[row]["groundSpeed"] = entry["groundSpeed"]
            changedRoles.append(TrafficModel.GroundSpeedRole)
        if self._trafficEntries[row]["verticalSpeed"] != entry["verticalSpeed"]:
            self._trafficEntries[row]["verticalSpeed"] = entry["verticalSpeed"]
            changedRoles.append(TrafficModel.VerticalSpeedRole)
        if self._trafficEntries[row]["squawk"] != entry["squawk"]:
            self._trafficEntries[row]["squawk"] = entry["squawk"]
            changedRoles.append(TrafficModel.SquawkRole)
        if self._trafficEntries[row]["alert"] != entry["alert"]:
            self._trafficEntries[row]["alert"] = entry["alert"]
            changedRoles.append(TrafficModel.AlertRole)
        if self._trafficEntries[row]["emergency"] != entry["emergency"]:
            self._trafficEntries[row]["emergency"] = entry["emergency"]
            changedRoles.append(TrafficModel.EmergencyRole)
        if self._trafficEntries[row]["spi"] != entry["spi"]:
            self._trafficEntries[row]["spi"] = entry["spi"]
            changedRoles.append(TrafficModel.SpiRole)
        if self._trafficEntries[row]["isOnGround"] != entry["isOnGround"]:
            self._trafficEntries[row]["isOnGround"] = entry["isOnGround"]
            changedRoles.append(TrafficModel.IsOnGroundRole)
        if self._trafficEntries[row]["lastSeen"] != entry["lastSeen"]:
            self._trafficEntries[row]["lastSeen"] = entry["lastSeen"]
            changedRoles.append(TrafficModel.LastSeenRole)
        if self._trafficEntries[row]["msgCount"] != entry["msgCount"]:
            self._trafficEntries[row]["msgCount"] = entry["msgCount"]
            changedRoles.append(TrafficModel.MsgCountRole)

        if len(changedRoles) > 0:
            logger.debug("update traffic entry {}".format(entry["id"]))
        self.dataChanged.emit(ix, ix, changedRoles)

    @pyqtSlot(int)
    def removeTrafficEntry(self, id):
        logger.debug("remove traffic entry {}".format(id))
        row = self._rowFromId(id)
        self.beginRemoveRows(QModelIndex(), row, row)
        del self._trafficEntries[row]
        self.endRemoveRows()

    @property
    def ids(self) -> list():
        return [t["id"] for t in self._trafficEntries]

    def _rowFromId(self, id):
        for index, item in enumerate(self._trafficEntries):
            if item["id"] == id:
                return index
        raise ValueError("no traffic entry for id {}".format(id))

    def _getImageSourcePath(self, model):
        path = os.path.join(self._aircraftImagesPath, "Aircraft {}".format(model))
        try:
            first_file = next((os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))), "default value here")
        except FileNotFoundError as ex:
            logger.warning(str(ex))
            first_file = ""
        return os.path.join(path, first_file)

    def _getCategoryName(self, category):
        """
        todo
        - surface_vehicle_emergency = 17
        - surface_vehicle_service = 18
        - point_obstacle = 19
        - cluster_obstacle = 20
        - line_obstacle = 21
        """
        if category == 0:
            return "No info"
        elif category == 1:
            return "Light"
        elif category == 2:
            return "Small"
        elif category == 3:
            return "Large"
        elif category == 4:
            return "High Vortex"
        elif category == 5:
            return "Heavy"
        elif category == 6:
            return "Highly Maneuverable"
        elif category == 7:
            return "Rotorcraft"
        elif category == 9:  # there is no 8
            return "Glider"
        elif category == 10:
            return "Lighter than air"
        elif category == 11:
            return "Sky Diver"
        elif category == 12:
            return "Paraglider"
        elif category == 14:  # there is no 13
            return "Unmanned"
        elif category == 15:
            return "Spaceship"
        else:
            return "Unknown category"
