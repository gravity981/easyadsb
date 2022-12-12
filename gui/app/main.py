import sys

from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtCore import Qt, QObject, QAbstractListModel, QModelIndex, pyqtProperty, pyqtSignal, pyqtSlot, QMetaObject, Q_ARG, QVariant
import mqtt
import json
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("logger")


def on_message(client, userdata, msg):
    if msg.topic == "/easyadsb/json/satellites":
        updateSatellites(msg)
    elif msg.topic == "/easyadsb/json/position":
        updatePosition(msg)
    elif msg.topic == "/easyadsb/json/traffic":
        updateTraffic(msg)


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
                    Q_ARG(int, sat["svid"]),
                    Q_ARG(QVariant, sat["cno"]),
                    Q_ARG(bool, sat["used"]),
                    Q_ARG(QVariant, sat["elevation"]),
                    Q_ARG(QVariant, sat["azimuth"]),
                )
            else:
                QMetaObject.invokeMethod(
                    satellitesModel,
                    "addSatellite",
                    Qt.QueuedConnection,
                    Q_ARG(int, sat["svid"]),
                    Q_ARG(QVariant, sat["cno"]),
                    Q_ARG(bool, sat["used"]),
                    Q_ARG(QVariant, sat["elevation"]),
                    Q_ARG(QVariant, sat["azimuth"]),
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
                QMetaObject.invokeMethod(trafficModel, "removeTrafficEntry", Qt.QueuedConnection, Q_ARG(int, id))
    except Exception as ex:
        logger.error("could not parse traffic message, {}".format(str(ex)))


class SatellitesModel(QAbstractListModel):
    countChanged = pyqtSignal()

    SvIdRole = Qt.UserRole + 1
    CnoRole = Qt.UserRole + 2
    IsUsedRole = Qt.UserRole + 3
    ElevationRole = Qt.UserRole + 4
    AzimuthRole = Qt.UserRole + 5

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
            return self._satellites[row]["isUsed"]
        if role == SatellitesModel.ElevationRole:
            return self._satellites[row]["elv"]
        if role == SatellitesModel.AzimuthRole:
            return self._satellites[row]["az"]

    def rowCount(self, parent=QModelIndex()):
        return len(self._satellites)

    def roleNames(self):
        return {
            SatellitesModel.SvIdRole: b"svid",
            SatellitesModel.CnoRole: b"cno",
            SatellitesModel.IsUsedRole: b"isUsed",
            SatellitesModel.ElevationRole: b"elv",
            SatellitesModel.AzimuthRole: b"az",
        }

    @pyqtProperty(int, notify=countChanged)
    def usedCount(self):
        return sum(map(lambda sat: sat["isUsed"], self._satellites))

    @pyqtProperty(int, notify=countChanged)
    def knownPosCount(self):
        return sum(map(lambda sat: sat["elv"] is not None and sat["az"] is not None, self._satellites))

    @pyqtSlot(int, QVariant, bool, QVariant, QVariant)
    def addSatellite(self, svid, cno, isUsed, elv, az):
        logger.info("add: svid={}, cno={}, used={}, elv={}, az={}".format(svid, cno, isUsed, elv, az))
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._satellites.append({"svid": svid, "elv": elv, "az": az, "cno": cno, "isUsed": isUsed})
        self.endInsertRows()

    @pyqtSlot(int, QVariant, bool, QVariant, QVariant)
    def updateSatellite(self, svid, cno, isUsed, elv, az):
        row = self._rowFromSvId(svid)
        ix = self.index(row, 0)
        changedRoles = []
        if self._satellites[row]["svid"] != svid:
            self._satellites[row]["svid"] = svid
            changedRoles.append(SatellitesModel.SvIdRole)
        if self._satellites[row]["elv"] != elv:
            self._satellites[row]["elv"] = elv
            changedRoles.append(SatellitesModel.ElevationRole)
        if self._satellites[row]["az"] != az:
            self._satellites[row]["az"] = az
            changedRoles.append(SatellitesModel.AzimuthRole)
        if self._satellites[row]["cno"] != cno:
            self._satellites[row]["cno"] = cno
            changedRoles.append(SatellitesModel.CnoRole)
        if self._satellites[row]["isUsed"] != isUsed:
            self._satellites[row]["isUsed"] = isUsed
            changedRoles.append(SatellitesModel.IsUsedRole)

        if len(changedRoles) > 0:
            logger.info("update: svid={}, cno={}, used={}, elv={}, az={}".format(svid, cno, isUsed, elv, az))
        self.dataChanged.emit(ix, ix, changedRoles)
        self.countChanged.emit()

    @pyqtSlot(int)
    def removeSatellite(self, svid):
        logger.info("remove " + str(svid))
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
        self._navMode = 1
        self._opMode = ""
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
        self._separationMeter = None
        self._utcTime = None

    @pyqtProperty(int, notify=positionChanged)
    def navMode(self):
        return self._navMode

    @pyqtProperty(str, notify=positionChanged)
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
    def separationMeter(self):
        return self._separationMeter

    @pyqtProperty(str, notify=positionChanged)
    def utcTime(self):
        return self._utcTime

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
        self._separationMeter = position["separationMeter"]
        self._utcTime = position["utcTime"]
        self.positionChanged.emit()


class TrafficModel(QAbstractListModel):
    IdRole = Qt.UserRole + 6
    CallsignRole = Qt.UserRole + 7
    ModelRole = Qt.UserRole + 8
    CategoryRole = Qt.UserRole + 9
    LatitudeRole = Qt.UserRole + 10
    LongitudeRole = Qt.UserRole + 11
    AltitudeRole = Qt.UserRole + 12
    TrackRole = Qt.UserRole + 13
    GroundSpeedRole = Qt.UserRole + 14
    VerticalSpeedRole = Qt.UserRole + 15
    SquawkRole = Qt.UserRole + 16
    AlertRole = Qt.UserRole + 17
    EmergencyRole = Qt.UserRole + 18
    SpiRole = Qt.UserRole + 19
    IsOnGroundRole = Qt.UserRole + 20
    LastSeenRole = Qt.UserRole + 21
    MsgCountRole = Qt.UserRole + 22

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
        logger.info("add traffic entry")
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
            logger.info("update traffic entry {}".format(entry["id"]))
        self.dataChanged.emit(ix, ix, changedRoles)

    @pyqtSlot(int)
    def removeTrafficEntry(self, id):
        logger.info("remove traffic entry {}".format(id))
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


app = QGuiApplication(sys.argv)
satellitesModel = SatellitesModel()
positionModel = PositionModel()
trafficModel = TrafficModel()
engine = QQmlApplicationEngine()
engine.rootContext().setContextProperty("satellitesModel", satellitesModel)
engine.rootContext().setContextProperty("positionModel", positionModel)
engine.rootContext().setContextProperty("trafficModel", trafficModel)
engine.quit.connect(app.quit)
engine.load("main.qml")
mqttClient = mqtt.launch("easyadsb-gui", "localhost", 1883)
mqttClient.on_message = on_message
mqttClient.subscribe("/easyadsb/json/satellites")
mqttClient.subscribe("/easyadsb/json/traffic")
mqttClient.subscribe("/easyadsb/json/position")

sys.exit(app.exec())
