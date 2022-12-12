from enum import IntEnum, Enum
import datetime
import threading
import logging
from pynmeagps import NMEAMessage
from copy import deepcopy

logger = logging.getLogger("logger")


class NavError(Exception):
    pass


class NavMode(IntEnum):
    """
    - NoFix = 1, no position
    - Fix2D = 2, 2D positoin (indicates low accuracy)
    - Fix3D = 3, 3D position (indicates high accuracy)
    """

    NoFix = 1
    Fix2D = 2
    Fix3D = 3


class OperationMode(str, Enum):
    """
    - Automatic = 'A', Automatically switching between 2D or 3D mode
    - Manual    = 'M', Manually set to operate in 2D or 3D mode
    """

    Automatic = "A"
    Manual = "M"


class SatInfo(dict):
    """
    Represents information about a Nav Satellite. Used within :class:`NavMonitor`
    """

    def __init__(self, svid: int = 0, elevation: int = 0, azimuth: int = 0, cno: int = 0, used: bool = False):
        self["svid"] = svid
        self["elevation"] = elevation
        self["azimuth"] = azimuth
        self["cno"] = cno
        self["used"] = used

    @property
    def id(self) -> int:
        """
        Ubx satellite number, svId
        """
        return self["svid"]

    @property
    def elevation(self) -> int:
        """
        Elevation in degrees, range 0 to 90
        """
        return self["elevation"]

    @property
    def azimuth(self) -> int:
        """
        Azimuth in degrees, range 0 to 359
        """
        return self["azimuth"]

    @property
    def cno(self) -> int:
        """
        Carrier to Noise Ratio in dbHz, Signal strength, range 0 to 99, null when not tracking
        """
        return self["cno"]

    @property
    def used(self) -> bool:
        """
        Used for navigation
        """
        return self["used"]

    def __str__(self):
        return "<Sat(id={}, elv={}, az={}, cno={}, used={})>".format(self["svid"], self["elevation"], self["azimuth"], self["cno"], self["used"])


class PosInfo(dict):
    def __init__(self):
        self["navMode"] = None
        self["opMode"] = None
        self["pdop"] = None
        self["hdop"] = None
        self["vdop"] = None
        self["trueTack"] = None
        self["magneticTrack"] = None
        self["groundSpeedKnots"] = None
        self["groundSpeedKph"] = None
        self["latitude"] = None
        self["longitude"] = None
        self["altitudeMeter"] = None
        self["separationMeter"] = None
        self["utcTime"] = None
        self["temperature"] = None
        self["humidity"] = None
        self["pressure"] = None
        self["pressureAltitude"] = None
        self._utcTime = None

    @property
    def navMode(self) -> NavMode:
        """
        Navigation Mode, see :class:`NavMode`
        """
        return self["navMode"]

    @property
    def opMode(self) -> OperationMode:
        """
        Operation Mode, see :class:`OperationMode`
        """
        return self["opMode"]

    @property
    def pdop(self) -> float:
        """
        Position Dilution of Precision
        """
        return self["pdop"]

    @property
    def hdop(self) -> float:
        """
        Horizontal Dilution of Precision
        """
        return self["hdop"]

    @property
    def vdop(self) -> float:
        """
        Vertical Dilution of Precision
        """
        return self["vdop"]

    @property
    def trueTrack(self) -> float:
        """
        Course over ground (true), can be None
        """
        return self["trueTack"]

    @property
    def magneticTrack(self) -> float:
        """
        Course over ground (magnetic), can be None
        """
        return self["magneticTrack"]

    @property
    def groundSpeedKnots(self) -> float:
        """
        Speed over ground in knots, can be None
        """
        return self["groundSpeedKnots"]

    @property
    def groundSpeedKph(self) -> float:
        """
        Speed over ground in kilometers per hour, can be None
        """
        return self["groundSpeedKph"]

    @property
    def latitude(self) -> float:
        """
        latitude in the format degrees, minutes and (decimal) fractions of minutes.
        Positive value is considered North, negative South
        can be None
        """
        return self["latitude"]

    @property
    def longitude(self) -> float:
        """
        longitude in the format degrees, minutes and (decimal) fractions of minutes.
        Positive value is considered East, negative West
        can be None
        """
        return self["longitude"]

    @property
    def altitudeMeter(self) -> float:
        """
        Altitude above mean sea level in meters, can be None
        """
        return self["altitudeMeter"]

    @property
    def separationMeter(self):
        """
        Geoid separation: difference between ellipsoid and mean sea level, can be None
        """
        return self["separationMeter"]

    @property
    def utcTime(self) -> datetime.time:
        """
        UTC time
        """
        return self._utcTime

    @property
    def temperature(self) -> float:
        """
        Temperature in °C
        """
        return self["temperature"]

    @property
    def humidity(self) -> float:
        """
        Humidity in %H
        """
        return self["humidity"]

    @property
    def pressure(self) -> float:
        """
        Pressure in hPa
        """
        return self["pressure"]

    @property
    def pressureAltitude(self) -> float:
        """
        Altitude calculated from `pressure` and `temperature` with reference to 1013.25 hPa
        """
        return self["pressureAltitude"]


class NavMonitor:
    """
    Monitor for satellite navigation. uses :class:`NMeaMessage` to update its state
    """

    def __init__(self):
        self._gsvMsgNum = 1
        self._satellites = dict()
        self._posInfo = PosInfo()
        self._lock = threading.Lock()
        self._observers = list()

        # fields for update cylce
        self._gsvDone = False
        self._gsaDone = False
        self._vtgDone = False
        self._ggaDone = False

    @property
    def satellites(self) -> dict:
        """
        Dictionary of :class:`SatInfo`
        """
        with self._lock:
            return deepcopy(self._satellites)

    @property
    def posInfo(self) -> PosInfo:
        """
        Current `PosInfo`
        """
        with self._lock:
            return deepcopy(self._posInfo)

    def register(self, obj):
        """
        Register an observer for `NavMonitor` updates
        """
        self._observers.append(obj)

    def updateBme(self, msg: dict):
        """
        update `NavMonitor` with BME280 json message
        """
        with self._lock:
            self._posInfo["temperature"] = msg["temperature"]
            self._posInfo["humidity"] = msg["humidity"]
            self._posInfo["pressure"] = msg["pressure"]
            self._posInfo["pressureAltitude"] = msg["pressureAltitude"]

    def update(self, msg: NMEAMessage):
        """
        update `NavMonitor` with an NMEAMessage. The following NMEA messages are supported:
        - GSV, satellites
        - GSA, used satellites
        - VTG, speed and track
        - GGA, position

        other messages will raise a :class:`NavError`
        """
        with self._lock:
            if msg.msgID == "GSV":
                self._updateGSV(msg)
            elif msg.msgID == "GSA":
                self._updateGSA(msg)
            elif msg.msgID == "VTG":
                self._updateVTG(msg)
            elif msg.msgID == "GGA":
                self._updateGGA(msg)

            if self._updateCylceDone():
                logger.debug("nav monitor update cycle done")
                self._resetUpdateCycle()
                self._notify()

    def _updateGSV(self, msg):
        # in sync
        if msg.msgNum == self._gsvMsgNum:
            # on first message
            if msg.msgNum == 1:
                self._gsvRemaningSVCount = msg.numSV
                self._intermediateSVs = dict()

            # on each message
            max = self._gsvRemaningSVCount if self._gsvRemaningSVCount < 4 else 4
            for i in range(1, max + 1):
                sv_id = int(getattr(msg, "svid_0{}".format(i)))
                sv_elv = getattr(msg, "elv_0{}".format(i))
                sv_elv = sv_elv if sv_elv else None
                sv_az = getattr(msg, "az_0{}".format(i))
                sv_az = sv_az if sv_az else None
                sv_cno = getattr(msg, "cno_0{}".format(i))
                sv_cno = sv_cno if sv_cno else None
                self._intermediateSVs[sv_id] = SatInfo(sv_id, sv_elv, sv_az, sv_cno)
            self._gsvRemaningSVCount -= max
            self._gsvMsgNum += 1

            # on last message
            if msg.msgNum == msg.numMsg:
                for sat in self._intermediateSVs.values():
                    if sat.id in self._satellites.keys():
                        NavMonitor._updateSatInfo(self._satellites[sat.id], sat)
                    else:
                        self._satellites[sat.id] = sat
                for k in list(self._satellites.keys()):
                    if k not in self._intermediateSVs.keys():
                        del self._satellites[k]
                if len(self._satellites) != msg.numSV:
                    logger.error("number of satellites does not match numSV from message")
                self._gsvDone = True
                self._gsvMsgNum = 1
        else:
            logger.warning("abort update satellites, message number out of sync")
            self._gsvMsgNum = 1
            self._gsvRemaningSVCount = 0

    def _updateSatInfo(existing: SatInfo, new: SatInfo):
        existing["azimuth"] = new.azimuth
        existing["elevation"] = new.elevation
        existing["cno"] = new.cno

    def _updateGSA(self, msg):
        oldNavMode = self._posInfo["navMode"]
        self._posInfo["navMode"] = NavMode(int(getattr(msg, "navMode")))
        self._posInfo["opMode"] = OperationMode(getattr(msg, "opMode"))
        self._posInfo["pdop"] = float(getattr(msg, "PDOP"))
        self._posInfo["hdop"] = float(getattr(msg, "HDOP"))
        self._posInfo["vdop"] = float(getattr(msg, "VDOP"))

        if oldNavMode != self._posInfo["navMode"]:
            logger.info("NavMode changed to {}".format(self._posInfo["navMode"]))

        # If less than 12 SVs are used for navigation, the remaining fields are left empty.
        # If more than 12 SVs are used for navigation, only the IDs of the first 12 are output.
        usedSatIds = list()
        for i in range(1, 13):
            usedId = int(getattr(msg, "svid_{0:02d}".format(i)) or -1)
            if usedId != -1:
                usedSatIds.append(usedId)
        for satId, sat in self._satellites.items():
            sat["used"] = True if satId in usedSatIds else False
        self._gsaDone = True

    def _updateVTG(self, msg):
        self._updateCourse(msg)
        self._updateSpeed(msg)
        self._vtgDone = True

    def _updateCourse(self, msg):
        trueTrack = getattr(msg, "cogt")
        self._posInfo["trueTack"] = float(trueTrack) if trueTrack else None
        magneticTrack = getattr(msg, "cogm")
        self._posInfo["magneticTrack"] = float(magneticTrack) if magneticTrack else None

    def _updateSpeed(self, msg):
        groundSpeedKnots = getattr(msg, "sogn")
        self._posInfo["groundSpeedKnots"] = float(groundSpeedKnots) if groundSpeedKnots else None
        groundSpeedKph = getattr(msg, "sogk")
        self._posInfo["groundSpeedKph"] = float(groundSpeedKph) if groundSpeedKph else None

    def _updateGGA(self, msg):
        lat = getattr(msg, "lat")
        ns = getattr(msg, "NS")
        lon = getattr(msg, "lon")
        ew = getattr(msg, "EW")
        alt = getattr(msg, "alt")
        altUnit = getattr(msg, "altUnit")
        sep = getattr(msg, "sep")
        sepUnit = getattr(msg, "sepUnit")
        utcTime = getattr(msg, "time")

        if ns:
            c = 1 if ns == "N" else -1
        lat = float(lat) if lat else None
        self._posInfo["latitude"] = c * lat if lat is not None else None

        if ew:
            c = 1 if ew == "E" else -1
        lon = float(lon) if lon else None
        self._posInfo["longitude"] = c * lon if lon is not None else None

        if altUnit and sepUnit:
            if altUnit != "M":
                raise NavError("altitude unit must be M")
            if sepUnit != altUnit:
                raise NavError("separation unit must be equal to altitude unit")

            self._posInfo["altitudeMeter"] = float(alt) if alt else None
            self._posInfo["separationMeter"] = float(sep) if sep else None
        else:
            self._posInfo["altitudeMeter"] = None
            self._posInfo["separationMeter"] = None

        if utcTime:
            self._posInfo["utcTime"] = utcTime.strftime("%H:%M:%S")
            self._posInfo._utcTime = utcTime
        else:
            self._posInfo["utcTime"] = None
            self._posInfo._utcTime = None
        self._ggaDone = True

    def _updateCylceDone(self):
        return self._gsvDone and self._gsaDone and self._vtgDone and self._ggaDone

    def _resetUpdateCycle(self):
        self._gsvDone = False
        self._gsaDone = False
        self._vtgDone = False
        self._ggaDone = False

    def _notify(self):
        for obj in self._observers:
            obj.notify(deepcopy(self._posInfo))

    def __str__(self):
        return (
            "NavMonitor<(navMode={}, opMode={}, pdop={}, hdop={}, vdop={}, tt={}, mt={}, gsN={},"
            "gsK={}, lat={}, lon={}, altM={}, sepM={}, "
            "time={}, satellites={})>"
        ).format(
            self._posInfo["navMode"],
            self._posInfo["opMode"],
            self._posInfo["pdop"],
            self._posInfo["hdop"],
            self._posInfo["vdop"],
            self._posInfo["trueTack"],
            self._posInfo["magneticTrack"],
            self._posInfo["groundSpeedKnots"],
            self._posInfo["groundSpeedKph"],
            self._posInfo["latitude"],
            self._posInfo["longitude"],
            self._posInfo["altitudeMeter"],
            self._posInfo["separationMeter"],
            self._posInfo["utcTime"],
            str(self._satellites),
        )
