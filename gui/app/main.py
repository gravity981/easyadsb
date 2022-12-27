import sys
import os
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtCore import Qt,  QMetaObject, Q_ARG, QVariant
import json
import logging
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


def on_message(client, userdata, msg):
    if "satellites" in msg.topic:
        updateSatellites(msg)
    elif "position" in msg.topic:
        updatePosition(msg)
    elif "traffic" in msg.topic:
        updateTraffic(msg)
    elif "system" in msg.topic:
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


log_level = str(os.getenv("GUI_LOG_LEVEL"))
mqttTopics = str(os.getenv("GUI_MQTT_TOPICS")).split(",")
aircraftImagesPath = str(os.getenv("GUI_AIRCRAFT_IMAGES_PATH"))
logconf.setup_logging(log_level)
logger = logging.getLogger("logger")

app = QGuiApplication(sys.argv)
satellitesModel = SatellitesModel()
positionModel = PositionModel()
trafficModel = TrafficModel(aircraftImagesPath)
systemModel = SystemModel(aliveTimeout=5000)
keyboardController = KeyboardController()
engine = QQmlApplicationEngine()
engine.rootContext().setContextProperty("satellitesModel", satellitesModel)
engine.rootContext().setContextProperty("positionModel", positionModel)
engine.rootContext().setContextProperty("trafficModel", trafficModel)
engine.rootContext().setContextProperty("systemModel", systemModel)
engine.rootContext().setContextProperty("keyboardController", keyboardController)
engine.quit.connect(app.quit)
engine.load("qml/main.qml")
mqtt.launchStart("easyadsb-gui", "localhost", 1883, mqttTopics, on_message)
sys.exit(app.exec())
