from enum import Enum
import datetime
import threading
import logging
from pynmeagps import NMEAMessage
from copy import deepcopy

logger = logging.getLogger("logger")


class NavError(Exception):
    pass


class NavMode(Enum):
    """
    - NoFix = 1, no position
    - Fix2D = 2, 2D positoin (indicates low accuracy)
    - Fix3D = 3, 3D position (indicates high accuracy)
    """

    NoFix = 1
    Fix2D = 2
    Fix3D = 3


class OperationMode(Enum):
    """
    - Automatic = 'A', Automatically switching between 2D or 3D mode
    - Manual    = 'M', Manually set to operate in 2D or 3D mode
    """

    Automatic = "A"
    Manual = "M"


class Satellite:
    """
    Represents information about a Nav Satellite. Used within :class:`NavMonitor`
    """

    def __init__(self, id: int = 0, elevation: int = 0, azimuth: int = 0, cno: int = 0, used: bool = False):
        self._id = id
        self._elevation = elevation
        self._azimuth = azimuth
        self._cno = cno
        self._used = used

    @property
    def id(self) -> int:
        """
        Ubx satellite number, svId
        """
        return self._id

    @property
    def elevation(self) -> int:
        """
        Elevation in degrees, range 0 to 90
        """
        return self._elevation

    @property
    def azimuth(self) -> int:
        """
        Azimuth in degrees, range 0 to 359
        """
        return self._azimuth

    @property
    def cno(self) -> int:
        """
        Carrier to Noise Ratio in dbHz, Signal strength, range 0 to 99, null when not tracking
        """
        return self._cno

    @property
    def used(self) -> bool:
        """
        Used for navigation
        """
        return self._used

    def __str__(self):
        return "<Sat(id={}, elv={}, az={}, cno={}, used={})>".format(self._id, self._elevation, self._azimuth, self._cno, self._used)

    def __repr__(self):
        return self.__str__()


# TODO make this an observable subject so that it's possible to subscribe for changes
class NavMonitor:
    """
    Monitor for satellite navigation. uses :class:`NMeaMessage` to update its state
    """

    def __init__(self):
        self._gsvMsgNum = 1
        self._satellites = dict()
        self._navMode = NavMode.NoFix
        self._opMode = OperationMode.Manual
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
        self._separationMeter = None
        self._utcTime = None
        self._lock = threading.Lock()

    @property
    def satellites(self) -> dict():
        """
        Dictionary of :class:`Satellite`
        """
        with self._lock:
            return deepcopy(self._satellites)

    @property
    def navMode(self) -> NavMode:
        """
        Navigation Mode, see :class:`NavMode`
        """
        with self._lock:
            return self._navMode

    @property
    def opMode(self) -> OperationMode:
        """
        Operation Mode, see :class:`OperationMode`
        """
        with self._lock:
            return self._opMode

    @property
    def pdop(self) -> float:
        """
        Position Dilution of Precision
        """
        with self._lock:
            return self._pdop

    @property
    def hdop(self) -> float:
        """
        Horizontal Dilution of Precision
        """
        with self._lock:
            return self._hdop

    @property
    def vdop(self) -> float:
        """
        Vertical Dilution of Precision
        """
        with self._lock:
            return self._vdop

    @property
    def trueTrack(self) -> float:
        """
        Course over ground (true), can be None
        """
        with self._lock:
            return self._trueTrack

    @property
    def magneticTrack(self) -> float:
        """
        Course over ground (magnetic), can be None
        """
        with self._lock:
            return self._magneticTrack

    @property
    def groundSpeedKnots(self) -> float:
        """
        Speed over ground in knots, can be None
        """
        with self._lock:
            return self._groundSpeedKnots

    @property
    def groundSpeedKph(self) -> float:
        """
        Speed over ground in kilometers per hour, can be None
        """
        with self._lock:
            return self._groundSpeedKph

    @property
    def latitude(self) -> float:
        """
        latitude in the format degrees, minutes and (decimal) fractions of minutes.
        Positive value is considered North, negative South
        can be None
        """
        with self._lock:
            return self._latitude

    @property
    def longitude(self) -> float:
        """
        longitude in the format degrees, minutes and (decimal) fractions of minutes.
        Positive value is considered East, negative West
        can be None
        """
        with self._lock:
            return self._longitude

    @property
    def altitudeMeter(self) -> float:
        """
        Altitude above mean sea level in meters, can be None
        """
        with self._lock:
            return self._altitudeMeter

    @property
    def separationMeter(self):
        """
        Geoid separation: difference between ellipsoid and mean sea level, can be None
        """
        with self._lock:
            return self._separationMeter

    @property
    def utcTime(self) -> datetime.time:
        """
        UTC time
        """
        with self._lock:
            return self._utcTime

    # TODO positioning should not know about NMEAMessage,
    # the interface to update should take an argument of type of this own module
    # this makes it possible to not only update positioning through nmea messages but other
    # sources as well
    def update(self, msg: NMEAMessage):
        """
        update TrafficMonitor with an NMEAMessage. The following NMEA messages are supported:
        - GSV
        - GSA
        - VTG
        - GGA

        other messages will raise a :class:`NavError`
        """
        with self._lock:
            if msg.msgID == "GSV":
                self._updateSatellites(msg)
            elif msg.msgID == "GSA":
                self._updateUsedSatellites(msg)
            elif msg.msgID == "VTG":
                self._updateCourse(msg)
                self._updateSpeed(msg)
            elif msg.msgID == "GGA":
                self._updatePosition(msg)

    def _updateSatellites(self, msg):
        # in sync
        if msg.msgNum == self._gsvMsgNum:
            # first message
            if msg.msgNum == 1:
                self._gsvRemaningSVCount = msg.numSV
                self._intermediateSVs = dict()

            # for each message
            max = self._gsvRemaningSVCount if self._gsvRemaningSVCount < 4 else 4
            for i in range(1, max + 1):
                sv_id = int(getattr(msg, "svid_0{}".format(i)))
                sv_elv = int(getattr(msg, "elv_0{}".format(i)) or 0)
                sv_az = int(getattr(msg, "az_0{}".format(i)) or 0)
                sv_cno = int(getattr(msg, "cno_0{}".format(i)) or 0)
                self._intermediateSVs[sv_id] = Satellite(sv_id, sv_elv, sv_az, sv_cno)
            self._gsvRemaningSVCount -= max
            self._gsvMsgNum += 1

            # last message
            if msg.msgNum == msg.numMsg:
                # update dict instead of replacing it
                for sat in self._intermediateSVs.values():
                    if sat.id in self._satellites.keys():
                        NavMonitor._updateSatellite(self._satellites[sat.id], sat)
                    else:
                        self._satellites[sat.id] = sat
                for k in list(self._satellites.keys()):
                    if k not in self._intermediateSVs.keys():
                        del self._satellites[k]
                if len(self._satellites) != msg.numSV:
                    logger.error("number of satellites does not match numSV from message")
                self._gsvMsgNum = 1
        else:
            logger.warning("abort update satellites, message number out of sync")
            self._gsvMsgNum = 1
            self._gsvRemaningSVCount = 0

    def _updateSatellite(existing: Satellite, new: Satellite):
        existing._azimuth = new.azimuth
        existing._elevation = new.elevation
        existing._cno = new.cno

    def _updateUsedSatellites(self, msg):
        oldNavMode = self._navMode
        self._navMode = NavMode(int(getattr(msg, "navMode")))
        self._opMode = OperationMode(getattr(msg, "opMode"))
        self._pdop = float(getattr(msg, "PDOP"))
        self._hdop = float(getattr(msg, "HDOP"))
        self._vdop = float(getattr(msg, "VDOP"))

        if oldNavMode != self._navMode:
            logger.info("NavMode changed to {}".format(self._navMode))

        # If less than 12 SVs are used for navigation, the remaining fields are left empty.
        # If more than 12 SVs are used for navigation, only the IDs of the first 12 are output.
        usedSatIds = list()
        for i in range(1, 13):
            usedId = int(getattr(msg, "svid_{0:02d}".format(i)) or -1)
            if usedId != -1:
                usedSatIds.append(usedId)
        for satId, sat in self._satellites.items():
            sat._used = True if satId in usedSatIds else False

    def _updateCourse(self, msg):
        trueTrack = getattr(msg, "cogt")
        self._trueTrack = float(trueTrack) if trueTrack else None
        magneticTrack = getattr(msg, "cogm")
        self._magneticTrack = float(magneticTrack) if magneticTrack else None

    def _updateSpeed(self, msg):
        groundSpeedKnots = getattr(msg, "sogn")
        self._groundSpeedKnots = float(groundSpeedKnots) if groundSpeedKnots else None
        groundSpeedKph = getattr(msg, "sogk")
        self._groundSpeedKph = float(groundSpeedKph) if groundSpeedKph else None

    def _updatePosition(self, msg):
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
        self._latitude = c * lat if lat is not None else None

        if ew:
            c = 1 if ew == "E" else -1
        lon = float(lon) if lon else None
        self._longitude = c * lon if lon is not None else None

        if altUnit and sepUnit:
            if altUnit != "M":
                raise NavError("altitude unit must be M")
            if sepUnit != altUnit:
                raise NavError("separation unit must be equal to altitude unit")

            self._altitudeMeter = float(alt) if alt else None
            self._separationMeter = float(sep) if sep else None
        else:
            self._altitudeMeter = None
            self._separationMeter = None

        self._utcTime = utcTime

    def __str__(self):
        return (
            "NavMonitor<(navMode={}, opMode={}, pdop={}, hdop={}, vdop={}, tt={}, mt={}, gsN={},"
            "gsK={}, lat={}, lon={}, altM={}, sepM={}, "
            "time={}, satellites={})>"
        ).format(
            self._navMode,
            self._opMode,
            self._pdop,
            self._hdop,
            self._vdop,
            self._trueTrack,
            self._magneticTrack,
            self._groundSpeedKnots,
            self._groundSpeedKph,
            self._latitude,
            self._longitude,
            self._altitudeMeter,
            self._separationMeter,
            self._utcTime,
            str(self._satellites),
        )
