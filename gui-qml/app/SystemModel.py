from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot, QVariant, QTimer
import logging as log
import sys
import concurrent

try:
    try:
        import common.mqtt as mqtt
    except ImportError:
        import mqtt
except ImportError:
    sys.path.insert(0, '../../common')
    import mqtt


class SystemModel(QObject):
    systemChanged = pyqtSignal()
    statusChanged = pyqtSignal()

    def __init__(self, messenger, systemTopic, aliveTimeout, parent=None):
        QObject.__init__(self, parent)
        self._wifi = dict()
        self._gdl90 = dict()
        self._resources = dict()
        self._isAlive = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._die)
        self._timer.setInterval(aliveTimeout)
        self._timer.start()
        self._messenger = messenger
        self._systemTopic = systemTopic

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

    @pyqtSlot(str, result=bool)
    def setCallsignFilter(self, cs):
        request = mqtt.RequestMessage("setCallsignFilter", {"callsign": cs})
        return self._sendRequest(request, self._systemTopic)

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

    def _die(self):
        self._isAlive = False
        self.statusChanged.emit()

    def _sendRequest(self, request, topic):
        try:
            response = self._messenger.sendRequestAndWait(topic, request)
            return response["success"]
        except concurrent.futures._base.TimeoutError:
            log.error("request {} timed out".format(request))
            return False
