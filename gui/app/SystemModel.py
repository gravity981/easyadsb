from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot, QVariant, QTimer
import logging as log


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
        log.debug("update system")
        self.systemChanged.emit()
