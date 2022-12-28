from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot, QVariant
import logging as log


class PositionModel(QObject):
    positionChanged = pyqtSignal()

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self._navMode = None
        self._opMode = None
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
        self._geoAltitude = None
        self._utcTime = None
        self._temperature = None
        self._humidity = None
        self._pressure = None
        self._pressureAltitude = None

    @pyqtProperty(QVariant, notify=positionChanged)
    def navMode(self):
        return self._navMode

    @pyqtProperty(QVariant, notify=positionChanged)
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
    def geoAltitude(self):
        return self._geoAltitude

    @pyqtProperty(QVariant, notify=positionChanged)
    def utcTime(self):
        return self._utcTime

    @pyqtProperty(QVariant, notify=positionChanged)
    def temperature(self):
        return self._temperature

    @pyqtProperty(QVariant, notify=positionChanged)
    def humidity(self):
        return self._humidity

    @pyqtProperty(QVariant, notify=positionChanged)
    def pressure(self):
        return self._pressure

    @pyqtProperty(QVariant, notify=positionChanged)
    def pressureAltitude(self):
        return self._pressureAltitude

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
        if position["separationMeter"] is not None and position["altitudeMeter"] is not None:
            self._geoAltitude = position["separationMeter"] + position["altitudeMeter"]
        else:
            self._geoAltitude = None
        self._utcTime = position["utcTime"]
        self._temperature = position["temperature"]
        self._humidity = position["humidity"]
        self._pressure = position["pressure"]
        self._pressureAltitude = position["pressureAltitude"]
        log.debug("update position")
        self.positionChanged.emit()
