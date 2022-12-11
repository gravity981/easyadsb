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
                logger.info("remove " + str(oldSvId))
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


class SatellitesModel(QAbstractListModel):
    testPropertyChanged = pyqtSignal()
    SvIdRole = Qt.UserRole + 1
    CnoRole = Qt.UserRole + 2
    IsUsedRole = Qt.UserRole + 3
    ElevationRole = Qt.UserRole + 4
    AzimuthRole = Qt.UserRole + 5

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self._testProperty = "test data"
        self._satellites = [
            {"svid": 20, "elv": 0.0, "az": 0.0, "cno": 23, "isUsed": False},
            {"svid": 17, "elv": 0.0, "az": 0.0, "cno": 65, "isUsed": True},
            {"svid": 12, "elv": 0.0, "az": 0.0, "cno": 55, "isUsed": True},
        ]

    @pyqtProperty(str, notify=testPropertyChanged)
    def testProperty(self):
        return self._testProperty

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

    @pyqtSlot(int)
    def removeSatellite(self, svid):
        row = self._rowFromSvId(svid)
        self.beginRemoveColumns(QModelIndex(), row, row)
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


app = QGuiApplication(sys.argv)
satellitesModel = SatellitesModel()
positionModel = PositionModel()
engine = QQmlApplicationEngine()
engine.rootContext().setContextProperty("satellitesModel", satellitesModel)
engine.rootContext().setContextProperty("positionModel", positionModel)
engine.quit.connect(app.quit)
engine.load("main.qml")
mqttClient = mqtt.launch("easyadsb-gui", "localhost", 1883)
mqttClient.on_message = on_message
mqttClient.subscribe("/easyadsb/json/satellites")
mqttClient.subscribe("/easyadsb/json/traffic")
mqttClient.subscribe("/easyadsb/json/position")

sys.exit(app.exec())
