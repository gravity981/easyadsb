import sys

from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtCore import Qt, QObject, QAbstractListModel, QModelIndex, pyqtProperty, pyqtSignal, pyqtSlot, QMetaObject, Q_ARG
import mqtt
import json
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("logger")


def on_message(client, userdata, msg):
    if msg.topic == "/easyadsb/json/satellites":
        updateSatellites(msg)


def updateSatellites(msg):
    try:
        raw = msg.payload.decode("UTF-8").strip()
        satellites = json.loads(raw)
        oldSvIds = satellitesModel.svids
        for sat in satellites:
            if sat["svid"] in oldSvIds:
                logger.info("edit " + str(sat["svid"]))
                QMetaObject.invokeMethod(
                    satellitesModel,
                    "editSatellite",
                    Qt.QueuedConnection,
                    Q_ARG(int, sat["svid"]),
                    Q_ARG(int, sat["cno"]),
                    Q_ARG(bool, sat["used"]),
                    Q_ARG(int, sat["elevation"]),
                    Q_ARG(int, sat["azimuth"]),
                )
            else:
                logger.info("add " + str(sat["svid"]))
                QMetaObject.invokeMethod(
                    satellitesModel,
                    "addSatellite",
                    Qt.QueuedConnection,
                    Q_ARG(int, sat["svid"]),
                    Q_ARG(int, sat["cno"]),
                    Q_ARG(bool, sat["used"]),
                    Q_ARG(int, sat["elevation"]),
                    Q_ARG(int, sat["azimuth"]),
                )
        svids = [s["svid"] for s in satellites]
        for oldSvId in oldSvIds:
            if oldSvId not in svids:
                logger.info("remove " + str(oldSvId))
                QMetaObject.invokeMethod(satellitesModel, "removeSatellite", Qt.QueuedConnection, Q_ARG(int, oldSvId))
    except Exception as ex:
        logger.error("could not parse satellites message, {}".format(str(ex)))


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
            {"svid": 20, "elv": 0, "az": 0, "cno": "23", "isUsed": False},
            {"svid": 17, "elv": 0, "az": 0, "cno": "65", "isUsed": True},
            {"svid": 12, "elv": 0, "az": 0, "cno": "55", "isUsed": True},
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

    @pyqtSlot(int, int, bool, int, int)
    def addSatellite(self, svid, cno, isUsed, elv, az):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._satellites.append({"svid": svid, "elv": elv, "az": az, "cno": cno, "isUsed": isUsed})
        self.endInsertRows()

    @pyqtSlot(int, int, bool, int, int)
    def editSatellite(self, svid, cno, isUsed, elv, az):
        row = self._rowFromSvId(svid)
        ix = self.index(row, 0)
        self._satellites[row] = {"svid": svid, "elv": elv, "az": az, "cno": cno, "isUsed": isUsed}
        self.dataChanged.emit(ix, ix, self.roleNames())

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


app = QGuiApplication(sys.argv)
satellitesModel = SatellitesModel()
engine = QQmlApplicationEngine()
engine.rootContext().setContextProperty("satellitesModel", satellitesModel)
engine.quit.connect(app.quit)
engine.load("main.qml")
mqttClient = mqtt.launch("easyadsb-gui", "localhost", 1883)
mqttClient.on_message = on_message
mqttClient.subscribe("/easyadsb/json/satellites")
mqttClient.subscribe("/easyadsb/json/traffic")

sys.exit(app.exec())
