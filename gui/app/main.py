import sys

from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtCore import Qt, QObject, QAbstractListModel, QModelIndex, pyqtProperty, pyqtSignal, pyqtSlot, QMetaObject, Q_ARG, QVariant, QTimer
import mqtt
import json
import logging
import threading
import time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("logger")

current_role_index = 0


def getNextRoleId():
    global current_role_index
    current_role_index += 1
    return Qt.UserRole + current_role_index


def on_message(client, userdata, msg):
    if msg.topic == "/easyadsb/json/satellites":
        updateSatellites(msg)
    elif msg.topic == "/easyadsb/json/position":
        updatePosition(msg)
    elif msg.topic == "/easyadsb/json/traffic":
        updateTraffic(msg)
    elif msg.topic == "/easyadsb/json/system":
        updateSystem(msg)


def updateSatellites(msg):
    try:
        raw = msg.payload.decode("UTF-8").strip()
        satellites = json.loads(raw)
        oldSvIds = satellitesModel.svids
        for sat in satellites:
            if sat["svid"] in oldSvIds:
                QMetaObject.invokeMethod(
                    satellitesModel,
                    "updateSatellite",
                    Qt.QueuedConnection,
                    Q_ARG(QVariant, sat),
                )
            else:
                QMetaObject.invokeMethod(
                    satellitesModel,
                    "addSatellite",
                    Qt.QueuedConnection,
                    Q_ARG(QVariant, sat),
                )
        svids = [s["svid"] for s in satellites]
        for oldSvId in oldSvIds:
            if oldSvId not in svids:
                QMetaObject.invokeMethod(satellitesModel, "removeSatellite", Qt.QueuedConnection, Q_ARG(int, oldSvId))
    except Exception as ex:
        logger.error("could not parse satellites message, {}".format(str(ex)))


def updatePosition(msg):
    try:
        position = json.loads(msg.payload.decode("utf-8").strip())
        QMetaObject.invokeMethod(
            positionModel,
            "updatePosition",
            Qt.QueuedConnection,
            Q_ARG(QVariant, position),
        )
    except Exception as ex:
        logger.error("could not parse position message, {}".format(str(ex)))


def updateTraffic(msg):
    try:
        raw = msg.payload.decode("utf-8").strip()
        entries = json.loads(raw)
        oldEntryIds = trafficModel.ids
        for entry in entries:
            if entry["id"] in oldEntryIds:
                QMetaObject.invokeMethod(trafficModel, "updateTrafficEntry", Qt.QueuedConnection, Q_ARG(QVariant, entry))
            else:
                QMetaObject.invokeMethod(trafficModel, "addTrafficEntry", Qt.QueuedConnection, Q_ARG(QVariant, entry))
        ids = [t["id"] for t in entries]
        for oldId in oldEntryIds:
            if oldId not in ids:
                QMetaObject.invokeMethod(trafficModel, "removeTrafficEntry", Qt.QueuedConnection, Q_ARG(int, oldId))
    except Exception as ex:
        logger.error("could not parse traffic message, {}".format(str(ex)))


def updateSystem(msg):
    try:
        system = json.loads(msg.payload.decode("utf-8").strip())
        QMetaObject.invokeMethod(
            systemModel,
            "updateSystem",
            Qt.QueuedConnection,
            Q_ARG(QVariant, system),
        )
    except Exception as ex:
        logger.error("could not parse system message, {}".format(str(ex)))


class SatellitesModel(QAbstractListModel):
    countChanged = pyqtSignal()

    SvIdRole = getNextRoleId()
    CnoRole = getNextRoleId()
    IsUsedRole = getNextRoleId()
    ElevationRole = getNextRoleId()
    AzimuthRole = getNextRoleId()
    PrnRole = getNextRoleId()

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


class PositionModel(QObject):
    positionChanged = pyqtSignal()

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self._navMode = None
        self._opMode = None
        self._pdop = None
        self._hdop = None
        self._vdop = None
        self._trueTrack = None
        self._magneticTrack = None
        self._groundSpeedKnots = None
        self._groundSpeedKph = None
        self._latitude = None
        self._longitude = None
        self._altitudeMeter = None
        self._geoAltitude = None
        self._utcTime = None
        self._temperature = None
        self._humidity = None
        self._pressure = None
        self._pressureAltitude = None

    @pyqtProperty(QVariant, notify=positionChanged)
    def navMode(self):
        return self._navMode

    @pyqtProperty(QVariant, notify=positionChanged)
    def opMode(self):
        return self._opMode

    @pyqtProperty(QVariant, notify=positionChanged)
    def pdop(self):
        return self._pdop

    @pyqtProperty(QVariant, notify=positionChanged)
    def hdop(self):
        return self._hdop

    @pyqtProperty(QVariant, notify=positionChanged)
    def vdop(self):
        return self._vdop

    @pyqtProperty(QVariant, notify=positionChanged)
    def trueTrack(self):
        return self._trueTrack

    @pyqtProperty(QVariant, notify=positionChanged)
    def magneticTrack(self):
        return self._magneticTrack

    @pyqtProperty(QVariant, notify=positionChanged)
    def groundSpeedKnots(self):
        return self._groundSpeedKnots

    @pyqtProperty(QVariant, notify=positionChanged)
    def groundSpeedKph(self):
        return self._groundSpeedKph

    @pyqtProperty(QVariant, notify=positionChanged)
    def latitude(self):
        return self._latitude

    @pyqtProperty(QVariant, notify=positionChanged)
    def longitude(self):
        return self._longitude

    @pyqtProperty(QVariant, notify=positionChanged)
    def altitudeMeter(self):
        return self._altitudeMeter

    @pyqtProperty(QVariant, notify=positionChanged)
    def geoAltitude(self):
        return self._geoAltitude

    @pyqtProperty(QVariant, notify=positionChanged)
    def utcTime(self):
        return self._utcTime

    @pyqtProperty(QVariant, notify=positionChanged)
    def temperature(self):
        return self._temperature

    @pyqtProperty(QVariant, notify=positionChanged)
    def humidity(self):
        return self._humidity

    @pyqtProperty(QVariant, notify=positionChanged)
    def pressure(self):
        return self._pressure

    @pyqtProperty(QVariant, notify=positionChanged)
    def pressureAltitude(self):
        return self._pressureAltitude

    @pyqtSlot(QVariant)
    def updatePosition(self, position):
        self._navMode = position["navMode"]
        self._opMode = position["opMode"]
        self._pdop = position["pdop"]
        self._hdop = position["hdop"]
        self._vdop = position["vdop"]
        self._trueTrack = position["trueTack"]
        self._magneticTrack = position["magneticTrack"]
        self._groundSpeedKnots = position["groundSpeedKnots"]
        self._groundSpeedKph = position["groundSpeedKph"]
        self._latitude = position["latitude"]
        self._longitude = position["longitude"]
        self._altitudeMeter = position["altitudeMeter"]
        if position["separationMeter"] is not None and position["altitudeMeter"] is not None:
            self._geoAltitude = position["separationMeter"] + position["altitudeMeter"]
        else:
            self._geoAltitude = None
        self._utcTime = position["utcTime"]
        self._temperature = position["temperature"]
        self._humidity = position["humidity"]
        self._pressure = position["pressure"]
        self._pressureAltitude = position["pressureAltitude"]
        self.positionChanged.emit()


class TrafficModel(QAbstractListModel):
    IdRole = getNextRoleId()
    CallsignRole = getNextRoleId()
    ModelRole = getNextRoleId()
    CategoryRole = getNextRoleId()
    LatitudeRole = getNextRoleId()
    LongitudeRole = getNextRoleId()
    AltitudeRole = getNextRoleId()
    TrackRole = getNextRoleId()
    GroundSpeedRole = getNextRoleId()
    VerticalSpeedRole = getNextRoleId()
    SquawkRole = getNextRoleId()
    AlertRole = getNextRoleId()
    EmergencyRole = getNextRoleId()
    SpiRole = getNextRoleId()
    IsOnGroundRole = getNextRoleId()
    LastSeenRole = getNextRoleId()
    MsgCountRole = getNextRoleId()

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self._trafficEntries = []

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        if role == TrafficModel.IdRole:
            return self._trafficEntries[row]["id"]
        if role == TrafficModel.CallsignRole:
            return self._trafficEntries[row]["callsign"]
        if role == TrafficModel.ModelRole:
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

    def rowCount(self, parent=QModelIndex()):
        return len(self._trafficEntries)

    def roleNames(self):
        return {
            TrafficModel.IdRole: b"id",
            TrafficModel.CallsignRole: b"callsign",
            TrafficModel.ModelRole: b"model",
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
        }

    @pyqtSlot(QVariant)
    def addTrafficEntry(self, entry):
        logger.debug("add traffic entry")
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._trafficEntries.append(entry)
        self.endInsertRows()

    @pyqtSlot(QVariant)
    def updateTrafficEntry(self, entry):
        row = self._rowFromId(entry["id"])
        ix = self.index(row, 0)
        changedRoles = []
        if self._trafficEntries[row]["id"] != entry["id"]:
            self._trafficEntries[row]["id"] = entry["id"]
            changedRoles.append(TrafficModel.IdRole)
        if self._trafficEntries[row]["callsign"] != entry["callsign"]:
            self._trafficEntries[row]["callsign"] = entry["callsign"]
            changedRoles.append(TrafficModel.CallsignRole)
        if self._trafficEntries[row]["model"] != entry["model"]:
            self._trafficEntries[row]["model"] = entry["model"]
            changedRoles.append(TrafficModel.ModelRole)
        if self._trafficEntries[row]["category"] != entry["category"]:
            self._trafficEntries[row]["category"] = entry["category"]
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


class SystemModel(QObject):
    systemChanged = pyqtSignal()

    def __init__(self, aliveTimeout, parent=None):
        QObject.__init__(self, parent)
        self._wifi = dict()
        self._gdl90 = dict()
        self._resources = dict()
        self._isAlive = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._die)
        self._timer.setInterval(aliveTimeout)
        self._timer.start()

    def _die(self):
        self._isAlive = False
        self.systemChanged.emit()

    @pyqtProperty(QVariant, notify=systemChanged)
    def wifi(self):
        return self._wifi

    @pyqtProperty(QVariant, notify=systemChanged)
    def gdl90(self):
        return self._gdl90

    @pyqtProperty(QVariant, notify=systemChanged)
    def resources(self):
        return self._resources

    @pyqtProperty(QVariant, notify=systemChanged)
    def isAlive(self):
        return self._isAlive

    @pyqtSlot(QVariant)
    def updateSystem(self, system):
        self._timer.start()
        self._isAlive = True
        self._wifi = system["wifi"]
        self._gdl90 = system["gdl90"]
        self._resources = system["resources"]
        self.systemChanged.emit()


app = QGuiApplication(sys.argv)
satellitesModel = SatellitesModel()
positionModel = PositionModel()
trafficModel = TrafficModel()
systemModel = SystemModel(aliveTimeout=5000)
engine = QQmlApplicationEngine()
engine.rootContext().setContextProperty("satellitesModel", satellitesModel)
engine.rootContext().setContextProperty("positionModel", positionModel)
engine.rootContext().setContextProperty("trafficModel", trafficModel)
engine.rootContext().setContextProperty("systemModel", systemModel)
engine.quit.connect(app.quit)
engine.load("main.qml")
topics = [
    "/easyadsb/json/satellites",
    "/easyadsb/json/traffic",
    "/easyadsb/json/position",
    "/easyadsb/json/system"
]
mqtt.launchStart("easyadsb-gui", "localhost", 1883, topics, on_message)
sys.exit(app.exec())
