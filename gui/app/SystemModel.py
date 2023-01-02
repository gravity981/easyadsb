from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot, QVariant, QTimer
import logging as log


class SystemModel(QObject):
    systemChanged = pyqtSignal()
    statusChanged = pyqtSignal()

    def __init__(self, messenger, aliveTimeout, parent=None):
        QObject.__init__(self, parent)
        self._messenger = messenger
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
        log.info("update status")
        self.statusChanged.emit()
