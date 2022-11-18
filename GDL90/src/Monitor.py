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
        latitude: float,
        longitude: float,
        altitude: int,
        track: int,
        groundSpeed: int
    ):
        self.id = id
        self.callsign = callsign
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.track = track
        self.groundSpeed = groundSpeed
        self.lastSeen = datetime.now()
        self.msgCount = 1
    
    def update(self, msg: SBSMessage):
        if self.id != msg.hexIdent:
            logger.warning("cannot update traffic entry with mismatching hexIdent")
            return
        # do not update callsign
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
        self.lastSeen = datetime.now()
        self.msgCount += 1

    def allFieldsSet() -> bool:
        # do not check callsign
        if msg.latitude == None:
            return False
        if msg.longitude == None:
            return False
        if msg.altitude == None:
            return False
        if msg.track == None:
            return False
        if msg.groundSpeed == None:
            return False
        return True

class TrafficMonitor:

    def __init__(self, ):
        self.traffic = dict()
        with open('/home/app/aircrafts.json') as json_file:
            self.db = json.load(json_file)
        self.cleanup()
    
    def cleanup(self):
        threading.Timer(10, self.cleanup).start()
        now = datetime.now()
        timeout = 300
        for k in list(self.traffic.keys()):
            trafficEntry = self.traffic[k]
            if trafficEntry.lastSeen < now - timedelta(seconds=timeout):
                logger.info("remove unseen traffic entry {id} / {cs} (older than {sec} seconds)".format(id=trafficEntry.id, cs=trafficEntry.callsign, sec=timeout))
                del self.traffic[k]

    def update(self, msg: SBSMessage):
        if msg.hexIdent in self.traffic:
            self.traffic[msg.hexIdent].update(msg)
        else:
            callsign = self.db[msg.hexIdent][0] if msg.hexIdent in self.db.keys() else None
            logger.info("add new traffic entry {id} / {cs}".format(id=msg.hexIdent, cs=callsign))
            self.traffic[msg.hexIdent] = TrafficEntry(msg.hexIdent, callsign, msg.latitude, msg.longitude, msg.altitude, msg.track, msg.groundSpeed)

