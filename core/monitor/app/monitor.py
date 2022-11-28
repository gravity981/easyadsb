from enum import Enum
from SBSProtocol import SBSMessage
from datetime import datetime, timedelta
import threading
import logging
import json
from pynmeagps import NMEAMessage
from copy import deepcopy

logger = logging.getLogger("logger")


class GPSNavMode(Enum):
    nofix = 1
    fix2D = 2
    fix3D = 3


class GpsOpMode(Enum):
    Automatic = 'A'
    Manual = 'M'


class GpsSatellite:
    def __init__(self, id: int = 0, elevation: int = 0, azimuth: int = 0, snr: int = 0, used: bool = False):
        self.id = id
        self.elevation = elevation
        self.azimuth = azimuth
        self.snr = snr
        self.used = used

    def __str__(self):
        return "<Sat(id={}, elv={}, az={}, snr={}, used={})>".format(self.id, self.elevation, self.azimuth, self.snr, self.used)

    def __repr__(self):
        return self.__str__()


class GpsMonitor:
    def __init__(self):
        self._gsvMsgNum = 1
        self._satellites = dict()
        self._navMode = GPSNavMode.nofix
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
    def satellites(self):
        with self._lock:
            return deepcopy(self._satellites)

    @property
    def navMode(self):
        with self._lock:
            return self._navMode

    @property
    def opMode(self):
        with self._lock:
            return self._opMode

    @property
    def pdop(self):
        with self._lock:
            return self._pdop

    @property
    def hdop(self):
        with self._lock:
            return self._hdop

    @property
    def vdop(self):
        with self._lock:
            return self._vdop

    @property
    def trueTrack(self):
        with self._lock:
            return self._trueTrack

    @property
    def magneticTrack(self):
        with self._lock:
            return self._magneticTrack

    @property
    def groundSpeedKnots(self):
        with self._lock:
            return self._groundSpeedKnots

    @property
    def groundSpeedKph(self):
        with self._lock:
            return self._groundSpeedKph

    @property
    def latitude(self):
        with self._lock:
            return self._latitude

    @property
    def longitude(self):
        with self._lock:
            return self._longitude

    @property
    def altitudeMeter(self):
        with self._lock:
            return self._altitudeMeter

    @property
    def separationMeter(self):
        """
        Geoid separation: difference between ellipsoid and mean sea level
        """
        with self._lock:
            return self._separationMeter

    @property
    def utcTime(self):
        with self._lock:
            return self._utcTime

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

    def update(self, msg: NMEAMessage):
        with self._lock:
            oldNavMode = self._navMode

            if msg.msgID == "GSV":
                self.updateSatellites(msg)
            elif msg.msgID == "GSA":
                self.updateActiveSatellites(msg)
            elif msg.msgID == "VTG":
                self.updateCourse(msg)
                self.updateSpeed(msg)
            elif msg.msgID == "GGA":
                self.updatePosition(msg)

            if oldNavMode != self._navMode:
                logger.info("GPS NavMode changed to {}".format(self._navMode))

    def updateSatellites(self, msg):
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
        existing.azimuth = new.azimuth
        existing.elevation = new.elevation
        existing.snr = new.snr

    def updateActiveSatellites(self, msg):
        self._navMode = GPSNavMode(int(getattr(msg, "navMode")))
        self._opMode = GpsOpMode(getattr(msg, "opMode"))
        self._pdop = getattr(msg, "PDOP")
        self._hdop = getattr(msg, "HDOP")
        self._vdop = getattr(msg, "VDOP")
        # assumption always maximal 12 possible used satellites
        usedSatIds = list()
        for i in range(1, 13):
            usedId = int(getattr(msg, "svid_{0:02d}".format(i)) or -1)
            if usedId != -1:
                usedSatIds.append(usedId)
        for satId, sat in self._satellites.items():
            sat.used = True if satId in usedSatIds else False

    def updateCourse(self, msg):
        trueTrack = getattr(msg, "cogt")
        self._trueTrack = int(trueTrack) if trueTrack else None
        magneticTrack = getattr(msg, "cogm")
        self._magneticTrack = int(magneticTrack) if magneticTrack else None

    def updateSpeed(self, msg):
        groundSpeedKnots = getattr(msg, "sogn")
        self._groundSpeedKnots = float(groundSpeedKnots) if groundSpeedKnots else None
        groundSpeedKph = getattr(msg, "sogk")
        self._groundSpeedKph = float(groundSpeedKph) if groundSpeedKph else None

    def updatePosition(self, msg):
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


class TrafficEntry:
    def __init__(self, id: str, callsign: str, model: str, category: int, latitude: float, longitude: float, altitude: int, track: int, groundSpeed: int):
        self.id = int(id, 16)
        self.callsign = callsign
        self.model = model
        self.category = category
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.track = track
        self.groundSpeed = groundSpeed
        self.lastSeen = datetime.now()
        self.msgCount = 1

    def update(self, msg: SBSMessage):
        if self.id != int(msg.hexIdent, 16):
            logger.warning("cannot update traffic entry with mismatching hexIdent")
            return
        if msg.latitude is not None:
            self.latitude = msg.latitude
        if msg.longitude is not None:
            self.longitude = msg.longitude
        if msg.altitude is not None:
            self.altitude = msg.altitude
        if msg.track is not None:
            self.track = msg.track
        if msg.groundSpeed is not None:
            self.groundSpeed = msg.groundSpeed
        self.lastSeen = datetime.utcnow()
        self.msgCount += 1

    # returns true if all relevant fields for a meaningful traffic information are set
    def ready(self) -> bool:
        if self.latitude is None:
            return False
        if self.longitude is None:
            return False
        if self.altitude is None:
            return False
        if self.track is None:
            return False
        if self.groundSpeed is None:
            return False
        return True

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
            self.id,
            self.callsign,
            self.model,
            self.category,
            self.latitude,
            self.longitude,
            self.altitude,
            self.track,
            self.groundSpeed,
            self.lastSeen,
            self.msgCount,
            self.ready(),
        )


class TrafficMonitor:
    def __init__(self):
        self.traffic = dict()
        with open("/home/data/aircrafts.json") as json_file:
            self.aircrafts_db = json.load(json_file)
        with open("/home/data/models.json") as json_file:
            self.models_db = json.load(json_file)
        self.cleanup()

    def cleanup(self):
        threading.Timer(10, self.cleanup).start()
        now = datetime.utcnow()
        timeout = 30
        for k in list(self.traffic.keys()):
            entry = self.traffic[k]
            if entry.lastSeen < now - timedelta(seconds=timeout):
                logger.info("remove {} (unseen for >{} seconds)".format(entry, timeout))
                del self.traffic[k]

    def update(self, msg: SBSMessage):
        if msg.hexIdent in self.traffic:
            entry = self.traffic[msg.hexIdent]
            wasReady = entry.ready()
            entry.update(msg)
            nowReady = entry.ready()
            if nowReady and not wasReady:
                logger.info("now ready {} ".format(entry))
        else:
            callsign, model, *_ = self.aircrafts_db[msg.hexIdent] if msg.hexIdent in self.aircrafts_db.keys() else [None, None]
            category, *_ = self.models_db[model] if model in self.models_db.keys() else [None]
            entry = TrafficEntry(msg.hexIdent, callsign, model, category, msg.latitude, msg.longitude, msg.altitude, msg.track, msg.groundSpeed)
            self.traffic[msg.hexIdent] = entry
            logger.info("add new {} (count {})".format(entry, len(self.traffic)))
