from enum import Enum
from SBSProtocol import SBSMessage
from datetime import datetime, timedelta
import threading
import logging
import json

logger = logging.getLogger("logger")

class GPSStatus(Enum):
    Active = 1
    Void = 0

class OwnshipMonitor:
    def __init__(self,
        status: GPSStatus,
        utc: str, # utc time
        latitude: float,
        longitude: float,
        groundSpeed: int, #knots
        track: int, #degrees
        date: str,
        magneticVariation: int # degrees
    ):
        pass

class SatellitesMonitor:
    def __init__(self,
        satellitesVisible: int,
        satellitesInUse: int,
        # per satellite
        prnNumber,
        elevation,
        azimuth,
        snr
    ):
        pass

class TrafficEntry:
    def __init__(self,
        id: str,
        callsign: str,
        model: str,
        category: int,
        latitude: float,
        longitude: float,
        altitude: int,
        track: int,
        groundSpeed: int
    ):
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
        if msg.latitude != None:
            self.latitude = msg.latitude
        if msg.longitude != None:
            self.longitude = msg.longitude
        if msg.altitude != None:
            self.altitude = msg.altitude
        if msg.track != None:
            self.track = msg.track
        if msg.groundSpeed != None:
            self.groundSpeed = msg.groundSpeed
        self.lastSeen = datetime.utcnow()
        self.msgCount += 1

    # returns true if all relevant fields for a meaningful traffic information are set
    def ready(self) -> bool:
        if self.latitude == None:
            return False
        if self.longitude == None:
            return False
        if self.altitude == None:
            return False
        if self.track == None:
            return False
        if self.groundSpeed == None:
            return False
        return True

    def __str__(self):
        return ("<TrafficEntry(id={:X}, "
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
            "ready={})>").format(
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
                self.ready()
            )

class TrafficMonitor:

    def __init__(self, ):
        self.traffic = dict()
        with open('/home/app/data/aircrafts.json') as json_file:
            self.aircrafts_db = json.load(json_file)
        with open('/home/app/data/models.json') as json_file:
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
            

