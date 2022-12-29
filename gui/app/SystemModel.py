from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot, QVariant, QTimer
import logging as log
import sys

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


class SystemModel(QObject):
    systemChanged = pyqtSignal()
    statusChanged = pyqtSignal()

    def __init__(self, sysCtrlTopic, messenger, aliveTimeout, parent=None):
        QObject.__init__(self, parent)
        self._messenger = messenger
        self._sysCtrlTopic = sysCtrlTopic
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
        self.statusChanged.emit()

    @pyqtProperty(QVariant, notify=systemChanged)
    def wifi(self):
        return self._wifi

    @pyqtProperty(QVariant, notify=statusChanged)
    def gdl90(self):
        return self._gdl90

    @pyqtProperty(QVariant, notify=systemChanged)
    def resources(self):
        return self._resources

    @pyqtProperty(QVariant, notify=statusChanged)
    def isAlive(self):
        return self._isAlive

    @pyqtSlot(QVariant)
    def onSystemUpdated(self, system):
        self._wifi = system["wifi"]
        self._resources = system["resources"]
        log.debug("update system")
        self.systemChanged.emit()

    @pyqtSlot(QVariant)
    def onStatusUpdated(self, status):
        self._timer.start()
        self._isAlive = True
        self._gdl90 = status["gdl90"]
        log.debug("update status")
        self.statusChanged.emit()

    @pyqtSlot(str, str)
    def addWifi(self, ssid, psk):
        request = mqtt.RequestMessage("addWifi", {"ssid": ssid, "psk": util.wpaPsk(ssid, psk).decode("utf-8")})
        response = self._messenger.sendRequestAndWait(self._sysCtrlTopic, request)
        return response["success"]
