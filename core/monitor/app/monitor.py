from enum import Enum
from SBSProtocol import SBSMessage
from datetime import datetime
import threading
import logging
import json
from pynmeagps import NMEAMessage
from copy import deepcopy

logger = logging.getLogger("logger")


class GpsNavMode(Enum):
    """
    NavMode, depending on the number of used satellites
    """
    NoFix = 1
    Fix2D = 2
    Fix3D = 3


class GpsOpMode(Enum):
    """
    Manual, 'M' = Manually set to operate in 2D or 3D mode
    Automatic, 'A' = Automatically switching between 2D or 3D mode
    """
    Automatic = 'A'
    Manual = 'M'


class GpsSatellite:
    """
    Represents information about a Gps Satellite. Used within :class:`GpsMonitor`
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


class GpsMonitor:
    """
    Monitor for satellite navigation. uses :class:`NMeaMessage` to update its state
    """
    def __init__(self):
        self._gsvMsgNum = 1
        self._satellites = dict()
        self._navMode = GpsNavMode.NoFix
        self._opMode = GpsOpMode.Manual
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
        Dictionary of :class:`GpsSatellite`
        """
        with self._lock:
            return deepcopy(self._satellites)

    @property
    def navMode(self) -> GpsNavMode:
        """
        Navigation Mode, see :class:`GpsNavMode`
        """
        with self._lock:
            return self._navMode

    @property
    def opMode(self) -> GpsOpMode:
        """
        Operation Mode, see :class:`GpsOpMode`
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

    def update(self, msg: NMEAMessage):
        """
        update TrafficMonitor with an NMEAMessage. The following MsgIDs are supported:
        - GSV
        - GSA
        - VTG
        - GGA

        other MsgIDs will be ignored
        """
        with self._lock:
            oldNavMode = self._navMode

            if msg.msgID == "GSV":
                self._updateSatellites(msg)
            elif msg.msgID == "GSA":
                self._updateUsedSatellites(msg)
            elif msg.msgID == "VTG":
                self._updateCourse(msg)
                self._updateSpeed(msg)
            elif msg.msgID == "GGA":
                self._updatePosition(msg)

            if oldNavMode != self._navMode:
                logger.info("GPS NavMode changed to {}".format(self._navMode))

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
                self._intermediateSVs[sv_id] = GpsSatellite(sv_id, sv_elv, sv_az, sv_cno)
            self._gsvRemaningSVCount -= max
            self._gsvMsgNum += 1

            # last message
            if msg.msgNum == msg.numMsg:
                # update dict instead of replacing it
                for sat in self._intermediateSVs.values():
                    if sat.id in self._satellites.keys():
                        GpsMonitor._updateSatellite(self._satellites[sat.id], sat)
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

    def _updateSatellite(existing: GpsSatellite, new: GpsSatellite):
        existing._azimuth = new.azimuth
        existing._elevation = new.elevation
        existing._cno = new.cno

    def _updateUsedSatellites(self, msg):
        self._navMode = GpsNavMode(int(getattr(msg, "navMode")))
        self._opMode = GpsOpMode(getattr(msg, "opMode"))
        self._pdop = float(getattr(msg, "PDOP"))
        self._hdop = float(getattr(msg, "HDOP"))
        self._vdop = float(getattr(msg, "VDOP"))

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
                raise Exception("altitude unit must be M")
            if sepUnit != altUnit:
                raise Exception("separation unit must be equal to altitude unit")

            self._altitudeMeter = float(alt) if alt else None
            self._separationMeter = float(sep) if sep else None
        else:
            self._altitudeMeter = None
            self._separationMeter = None

        self._utcTime = utcTime

    def __str__(self):
        return (
            "GpsMonitor<(navMode={}, opMode={}, pdop={}, hdop={}, vdop={}, tt={}, mt={}, gsN={}," "gsK={}, lat={}, lon={}, altM={}, sepM={}, "
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


class TrafficError(Exception):
    pass


class TrafficCategory(Enum):
    no_info = 0
    light = 1
    small = 2
    large = 3
    high_vortex_large = 4
    heavy = 5
    highly_maneuverable = 6
    rotorcraft = 7
    # unassigned 8
    glider = 9
    lighter_than_air = 10
    sky_diver = 11
    paraglider = 12
    # unassigned 13
    unmanned = 14
    spaceship = 15
    # unassigned 16
    surface_vehicle_emergency = 17
    surface_vehicle_service = 18
    point_obstacle = 19
    cluster_obstacle = 20
    line_obstacle = 21
    # reserved 22 to 39


class TrafficEntry:
    def __init__(
        self,
        id: str,
        callsign: str,
        model: str,
        category: TrafficCategory,
        latitude: float,
        longitude: float,
        altitude: int,
        track: int,
        groundSpeed: int
    ):
        self._id = int(id, 16)
        self._callsign = callsign
        self._model = model
        self._category = category
        self._latitude = latitude
        self._longitude = longitude
        self._altitude = altitude
        self._track = track
        self._groundSpeed = groundSpeed
        self._lastSeen = datetime.now()
        self._msgCount = 1

    @property
    def id(self) -> int:
        """
        Transponder ID
        """
        return self._id

    @property
    def callsign(self) -> str:
        """
        Callsign, can be None
        """
        return self._callsign

    @property
    def model(self) -> str:
        """
        ICAO Type designator, can be None
        """
        return self._model

    @property
    def category(self) -> TrafficCategory:
        """
        See :class:`TrafficCategory`, can be None
        """
        return self._category

    @property
    def latitude(self) -> float:
        """
        latitude in the format degrees and (decimal) fraction
        Positive value is considered North, negative South
        can be None
        """
        return self._latitude

    @property
    def longitude(self) -> float:
        """
        longitude in the format degrees and (decimal) fraction
        Positive value is considered East, negative West
        can be None
        """
        return self._longitude

    @property
    def altitude(self) -> int:
        """
        Altitude above mean sea level in ft (referenced to 29.92 inches Hg)
        """
        return self._altitude

    @property
    def track(self) -> int:
        """
        Track in degrees from 0 to 360
        """
        return self._track

    @property
    def groundSpeed(self):
        """
        Ground Speed in knots
        """
        return self._groundSpeed

    @property
    def lastSeen(self) -> datetime:
        """
        seconds since last message about this :class:`TrafficEntry`
        """
        return (datetime.utcnow() - self._lastSeen).total_seconds()

    @property
    def msgCount(self):
        """
        Number of messages about this :class:`TrafficEntry`
        """
        return self._msgCount

    @property
    def ready(self) -> bool:
        """
        Returns true if all relevant fields for a meaningful traffic information are set
        """
        if self._latitude is None:
            return False
        if self._longitude is None:
            return False
        if self._altitude is None:
            return False
        if self._track is None:
            return False
        if self._groundSpeed is None:
            return False
        return True

    def update(self, msg: SBSMessage):
        """
        Update :class:`TrafficEntry` from :class:`SBSMessage`.
        Will raise :class:`TrafficError` on transponder ID mismatch
        """
        if self._id != int(msg.hexIdent, 16):
            raise TrafficError("Cannot update traffic entry with mismatching hexIdent")
        if msg.latitude is not None:
            self._latitude = msg.latitude
        if msg.longitude is not None:
            self._longitude = msg.longitude
        if msg.altitude is not None:
            self._altitude = msg.altitude
        if msg.track is not None:
            self._track = msg.track
        if msg.groundSpeed is not None:
            self._groundSpeed = msg.groundSpeed
        self._lastSeen = datetime.utcnow()
        self._msgCount += 1

    def __str__(self):
        return (
            "<TrafficEntry(id={:X}, "
            "cs={}, "
            "mdl={}, "
            "cat={}, "
            "lat={}, "
            "lon={}, "
            "alt={}, "
            "trk={}, "
            "spd={}, "
            "lastSeen={:%H:%M:%S}, "
            "msgCount={}, "
            "ready={})>"
        ).format(
            self._id,
            self._callsign,
            self._model,
            self._category,
            self._latitude,
            self._longitude,
            self._altitude,
            self._track,
            self._groundSpeed,
            self._lastSeen,
            self._msgCount,
            self.ready,
        )


class TrafficMonitor:
    """
    Monitors Flight Traffic. Can be updated with :class:`SBSMessage`
    """
    def __init__(self):
        self._traffic = dict()
        self._lock = threading.Lock()
        with open("/home/data/aircrafts.json") as json_file:
            self._aircrafts_db = json.load(json_file)
        with open("/home/data/models.json") as json_file:
            self._models_db = json.load(json_file)
        self._cleanup()

    @property
    def traffic(self) -> dict():
        """
        Dictionary of :class:`TrafficEntry`
        """
        with self._lock:
            return deepcopy(self._traffic)

    def update(self, msg: SBSMessage):
        """
        Update :class:`TrafficMonitor` from :class:`SBSMessage`
        """
        with self._lock:
            if msg.hexIdent in self._traffic:
                entry = self._traffic[msg.hexIdent]
                wasReady = entry.ready
                entry.update(msg)
                nowReady = entry.ready
                if nowReady and not wasReady:
                    logger.info("now ready {} ".format(entry))
            else:
                callsign, model, *_ = self._aircrafts_db[msg.hexIdent] if msg.hexIdent in self._aircrafts_db.keys() else [None, None]
                category, *_ = self._models_db[model] if model in self._models_db.keys() else [None]
                entry = TrafficEntry(msg.hexIdent, callsign, model, category, msg.latitude, msg.longitude, msg.altitude, msg.track, msg.groundSpeed)
                self._traffic[msg.hexIdent] = entry
                logger.info("add new {} (count {})".format(entry, len(self._traffic)))

    def _cleanup(self):
        threading.Timer(10, self._cleanup).start()
        with self._lock:
            timeout = 30
            for k in list(self._traffic.keys()):
                entry = self._traffic[k]
                if entry.lastSeen > timeout:
                    logger.info("remove {} (unseen for >{} seconds)".format(entry, timeout))
                    del self._traffic[k]
