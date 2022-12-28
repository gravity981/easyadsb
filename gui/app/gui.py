import sys
import os
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtCore import Qt,  QMetaObject, Q_ARG, QVariant
import json
import logging as log
from PositionModel import PositionModel
from SatellitesModel import SatellitesModel
from SystemModel import SystemModel
from TrafficModel import TrafficModel
from KeyboardController import KeyboardController

try:
    try:
        import common.mqtt as mqtt
        import common.logconf as logconf
    except ImportError:
        import mqtt
        import logconf
except ImportError:
    sys.path.insert(0, '../../common')
    import mqtt
    import logconf


class MessageDispatcher:
    """
    prase and dispatch incoming mqtt messages to correct receiver
    """

    def __init__(self, satellitesModel, trafficModel, positionModel, systemModel):
        self._satellitesModel = satellitesModel
        self._trafficModel = trafficModel
        self._positionModel = positionModel
        self._systemModel = systemModel

    def onMessage(self, client, userdata, msg):
        if "satellites" in msg.topic:
            self._updateSatellites(msg)
        elif "position" in msg.topic:
            self._updatePosition(msg)
        elif "traffic" in msg.topic:
            self._updateTraffic(msg)
        elif "sysmgmt" in msg.topic:
            self._updateSystem(msg)
        elif "status" in msg.topic:
            self._updateStatus(msg)

    def _updateSatellites(self, msg):
        try:
            raw = msg.payload.decode("UTF-8").strip()
            satellites = json.loads(raw)
            oldSvIds = self._satellitesModel.svids
            for sat in satellites:
                if sat["svid"] in oldSvIds:
                    QMetaObject.invokeMethod(
                        self._satellitesModel,
                        "updateSatellite",
                        Qt.QueuedConnection,
                        Q_ARG(QVariant, sat),
                    )
                else:
                    QMetaObject.invokeMethod(
                        self._satellitesModel,
                        "addSatellite",
                        Qt.QueuedConnection,
                        Q_ARG(QVariant, sat),
                    )
            svids = [s["svid"] for s in satellites]
            for oldSvId in oldSvIds:
                if oldSvId not in svids:
                    QMetaObject.invokeMethod(self._satellitesModel, "removeSatellite", Qt.QueuedConnection, Q_ARG(int, oldSvId))
        except Exception as ex:
            log.error("could not parse satellites message, {}".format(str(ex)))

    def _updatePosition(self, msg):
        try:
            position = json.loads(msg.payload.decode("utf-8").strip())
            QMetaObject.invokeMethod(
                self._positionModel,
                "updatePosition",
                Qt.QueuedConnection,
                Q_ARG(QVariant, position),
            )
        except Exception as ex:
            log.error("could not parse position message, {}".format(str(ex)))

    def _updateTraffic(self, msg):
        try:
            raw = msg.payload.decode("utf-8").strip()
            entries = json.loads(raw)
            oldEntryIds = self._trafficModel.ids
            for entry in entries:
                if entry["id"] in oldEntryIds:
                    QMetaObject.invokeMethod(self._trafficModel, "updateTrafficEntry", Qt.QueuedConnection, Q_ARG(QVariant, entry))
                else:
                    QMetaObject.invokeMethod(self._trafficModel, "addTrafficEntry", Qt.QueuedConnection, Q_ARG(QVariant, entry))
            ids = [t["id"] for t in entries]
            for oldId in oldEntryIds:
                if oldId not in ids:
                    QMetaObject.invokeMethod(self._trafficModel, "removeTrafficEntry", Qt.QueuedConnection, Q_ARG(int, oldId))
        except Exception as ex:
            log.error("could not parse traffic message, {}".format(str(ex)))

    def _updateSystem(self, msg):
        try:
            system = json.loads(msg.payload.decode("utf-8").strip())
            QMetaObject.invokeMethod(
                self._systemModel,
                "updateSystem",
                Qt.QueuedConnection,
                Q_ARG(QVariant, system),
            )
        except Exception as ex:
            log.error("could not parse system message, {}".format(str(ex)))

    def _updateStatus(self, msg):
        try:
            status = json.loads(msg.payload.decode("utf-8").strip())
            QMetaObject.invokeMethod(
                self._systemModel,
                "updateStatus",
                Qt.QueuedConnection,
                Q_ARG(QVariant, status),
            )
        except Exception as ex:
            log.error("could not parse status message, {}".format(str(ex)))


def main():
    log_level = str(os.getenv("GUI_LOG_LEVEL"))
    mqttTopics = str(os.getenv("GUI_MQTT_TOPICS")).split(",")
    aircraftImagesPath = str(os.getenv("GUI_AIRCRAFT_IMAGES_PATH"))
    logconf.setupLogging(log_level)

    app = QGuiApplication(sys.argv)
    satellitesModel = SatellitesModel()
    positionModel = PositionModel()
    trafficModel = TrafficModel(aircraftImagesPath)
    systemModel = SystemModel(aliveTimeout=5000)
    msgDispatcher = MessageDispatcher(satellitesModel, trafficModel, positionModel, systemModel)
    keyboardController = KeyboardController()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("satellitesModel", satellitesModel)
    engine.rootContext().setContextProperty("positionModel", positionModel)
    engine.rootContext().setContextProperty("trafficModel", trafficModel)
    engine.rootContext().setContextProperty("systemModel", systemModel)
    engine.rootContext().setContextProperty("keyboardController", keyboardController)
    engine.quit.connect(app.quit)
    engine.load("qml/main.qml")
    mqtt.launchStart("easyadsb-gui", "localhost", 1883, mqttTopics, msgDispatcher.onMessage)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
