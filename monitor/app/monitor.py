from enum import Enum
from SBSProtocol import SBSMessage
from datetime import datetime, timedelta
import threading
import logging
import json
from pynmeagps import NMEAMessage

logger = logging.getLogger("logger")


class GPSNavMode(Enum):
    nofix = 1
    fix2D = 2
    fix3D = 3


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
        self.satellites = dict()
        self.navMode = GPSNavMode.nofix
        self.opMode = None
        self.pdop = None
        self.hdop = None
        self.vdop = None
        self.trueTrack = None
        self.magneticTrack = None
        self.groundSpeedKnots = None
        self.groundSpeedKph = None
        self.latitude = None
        self.longitude = None
        self.altitudeMeter = None
        self.separationMeter = None

    def __str__(self):
        return (
            "GpsMonitor<(navMode={}, opMode={}, pdop={}, hdop={}, vdop={}, tt={}, mt={}, gsN={}," "gsK={}, lat={}, lon={}, altM={}, sepM={}, satellites={})>"
        ).format(
            self.navMode,
            self.opMode,
            self.pdop,
            self.hdop,
            self.vdop,
            self.trueTrack,
            self.magneticTrack,
            self.groundSpeedKnots,
            self.groundSpeedKph,
            self.latitude,
            self.longitude,
            self.altitudeMeter,
            self.separationMeter,
            str(self.satellites),
        )

    def update(self, msg: NMEAMessage):
        oldNavMode = self.navMode

        if msg.msgID == "GSV":
            self.updateSatellites(msg)
        if msg.msgID == "GSA":
            self.updateActiveSatellites(msg)
        if msg.msgID == "VTG":
            self.updateCourse(msg)
            self.updateSpeed(msg)
        if msg.msgID == "GGA":
            self.updatePosition(msg)

        if oldNavMode != self.navMode:
            logger.info("GPS NavMode changed to {}".format(self.navMode))

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
                    if sat.id in self.satellites.keys():
                        GpsMonitor._updateSatellite(self.satellites[sat.id], sat)
                    else:
                        self.satellites[sat.id] = sat
                for k in list(self.satellites.keys()):
                    if k not in self._intermediateSVs.keys():
                        del self.satellites[k]
                if len(self.satellites) != msg.numSV:
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
        self.navMode = GPSNavMode(int(getattr(msg, "navMode")))
        self.opMode = getattr(msg, "opMode")
        self.pdop = getattr(msg, "PDOP")
        self.hdop = getattr(msg, "HDOP")
        self.vdop = getattr(msg, "VDOP")
        # assumption always maximal 12 possible used satellites
        usedSatIds = list()
        for i in range(1, 13):
            usedId = int(getattr(msg, "svid_{0:02d}".format(i)) or -1)
            if usedId != -1:
                usedSatIds.append(usedId)
        for satId, sat in self.satellites.items():
            sat.used = True if satId in usedSatIds else False

    def updateCourse(self, msg):
        trueTrack = getattr(msg, "cogt")
        self.trueTrack = int(trueTrack) if trueTrack else None
        magneticTrack = getattr(msg, "cogm")
        self.magneticTrack = int(magneticTrack) if magneticTrack else None

    def updateSpeed(self, msg):
        groundSpeedKnots = getattr(msg, "sogn")
        self.groundSpeedKnots = float(groundSpeedKnots) if groundSpeedKnots else None
        groundSpeedKph = getattr(msg, "sogk")
        self.groundSpeedKph = float(groundSpeedKph) if groundSpeedKph else None

    def updatePosition(self, msg):
        lat = getattr(msg, "lat")
        ns = getattr(msg, "NS")
        lon = getattr(msg, "lon")
        ew = getattr(msg, "EW")
        alt = getattr(msg, "alt")
        altUnit = getattr(msg, "altUnit")
        sep = getattr(msg, "sep")
        sepUnit = getattr(msg, "sepUnit")

        if ns:
            c = 1 if ns == "N" else -1
        lat = float(lat) if lat else None
        self.latitude = c * lat if lat is not None else None

        if ew:
            c = 1 if ew == "E" else -1
        lon = float(lon) if lon else None
        self.longitude = c * lon if lon is not None else None

        if altUnit and sepUnit:
            if altUnit != "M":
                raise Exception("altitude unit must be M")
            if sepUnit != altUnit:
                raise Exception("separation unit must be equal to altitude unit")

            self.altitudeMeter = float(alt) if alt else None
            self.separationMeter = float(sep) if sep else None
        else:
            self.altitudeMeter = None
            self.separationMeter = None


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
