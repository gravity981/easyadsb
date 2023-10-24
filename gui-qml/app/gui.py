import sys
import os
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtCore import Qt, QVariant, pyqtSignal, QObject
from PositionModel import PositionModel
from SatellitesModel import SatellitesModel
from SystemModel import SystemModel
from TrafficModel import TrafficModel
from KeyboardController import KeyboardController
from WifiSettingsModel import WifiSettingsModel
import json

try:
    try:
        import common.mqtt as mqtt
        import common.util as util
    except ImportError:
        import mqtt
        import util
except ImportError:
    sys.path.insert(0, '../../common')
    import mqtt
    import util


class MessageDispatcher(QObject):
    """
    parse and dispatch incoming mqtt messages to correct receiver
    """

    satellitesUpdated = pyqtSignal(QVariant)
    positionUpdated = pyqtSignal(QVariant)
    trafficEntriesUpdated = pyqtSignal(QVariant)
    statusUpdated = pyqtSignal(QVariant)
    systemUpdated = pyqtSignal(QVariant)
    wifilistUpdated = pyqtSignal(QVariant)

    def __init__(self, parent=None):
        QObject.__init__(self, parent)

    def updateSatellites(self, msg):
        satellites = json.loads(msg)
        self.satellitesUpdated.emit(satellites)

    def updatePosition(self, msg):
        position = json.loads(msg)
        self.positionUpdated.emit(position)

    def updateTraffic(self, msg):
        entries = json.loads(msg)
        self.trafficEntriesUpdated.emit(entries)

    def updateSystem(self, msg):
        system = json.loads(msg)
        self.systemUpdated.emit(system)
        self.wifilistUpdated.emit(system)

    def updateStatus(self, msg):
        status = json.loads(msg)
        self.statusUpdated.emit(status)


def main():
    log_level = str(os.getenv("GUI_LOG_LEVEL"))
    satelliteTopic = str(os.getenv("GUI_MQTT_SATELLITE_TOPIC"))
    trafficTopic = str(os.getenv("GUI_MQTT_TRAFFIC_TOPIC"))
    positionTopic = str(os.getenv("GUI_MQTT_POSITION_TOPIC"))
    statusTopic = str(os.getenv("GUI_MQTT_STATUS_TOPIC"))
    sysInfoTopic = str(os.getenv("GUI_MQTT_SYSMGMT_INFO_TOPIC"))
    sysCtrlTopic = str(os.getenv("GUI_MQTT_SYSMGMT_CTRL_TOPIC"))
    aircraftImagesPath = str(os.getenv("GUI_AIRCRAFT_IMAGES_PATH"))
    util.setupLogging(log_level)

    trafficCtrlTopic = trafficTopic + "/ctrl"

    msgDispatcher = MessageDispatcher()
    subscriptions = {
        satelliteTopic: {
            "type": mqtt.MqttMessenger.NOTIFICATION,
            "func": msgDispatcher.updateSatellites
        },
        trafficTopic: {
            "type": mqtt.MqttMessenger.NOTIFICATION,
            "func": msgDispatcher.updateTraffic
        },
        trafficCtrlTopic: {
            "type": mqtt.MqttMessenger.RESPONSE,
        },
        positionTopic: {
            "type": mqtt.MqttMessenger.NOTIFICATION,
            "func": msgDispatcher.updatePosition
        },
        statusTopic: {
            "type": mqtt.MqttMessenger.NOTIFICATION,
            "func": msgDispatcher.updateStatus
        },
        sysInfoTopic: {
            "type": mqtt.MqttMessenger.NOTIFICATION,
            "func": msgDispatcher.updateSystem
        },
        sysCtrlTopic: {
            "type": mqtt.MqttMessenger.RESPONSE,
        },
    }
    mqClient = mqtt.launch("easyadsb-gui", "localhost", 1883)
    messenger = mqtt.MqttMessenger(mqClient, subscriptions)
    app = QGuiApplication(sys.argv)
    satellitesModel = SatellitesModel()
    positionModel = PositionModel()
    trafficModel = TrafficModel(messenger, trafficCtrlTopic, aircraftImagesPath)
    systemModel = SystemModel(messenger, trafficCtrlTopic, aliveTimeout=5000)
    wifiSettingsModel = WifiSettingsModel(messenger, sysCtrlTopic)
    msgDispatcher.satellitesUpdated.connect(satellitesModel.onSatellitesUpdated, Qt.QueuedConnection)
    msgDispatcher.positionUpdated.connect(positionModel.onPositionUpdated, Qt.QueuedConnection)
    msgDispatcher.trafficEntriesUpdated.connect(trafficModel.onTrafficEntriesUpdated, Qt.QueuedConnection)
    msgDispatcher.statusUpdated.connect(systemModel.onStatusUpdated, Qt.QueuedConnection)
    msgDispatcher.systemUpdated.connect(systemModel.onSystemUpdated, Qt.QueuedConnection)
    msgDispatcher.wifilistUpdated.connect(wifiSettingsModel.onWifiListUpdated, Qt.QueuedConnection)
    keyboardController = KeyboardController()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("satellitesModel", satellitesModel)
    engine.rootContext().setContextProperty("positionModel", positionModel)
    engine.rootContext().setContextProperty("trafficModel", trafficModel)
    engine.rootContext().setContextProperty("systemModel", systemModel)
    engine.rootContext().setContextProperty("keyboardController", keyboardController)
    engine.rootContext().setContextProperty("wifiSettingsModel", wifiSettingsModel)
    engine.quit.connect(app.quit)
    engine.load("qml/main.qml")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
