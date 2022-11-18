from enum import Enum
from SBSReader import SBSMessage
from datetime import datetime, timedelta
import threading
import logging

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
    
    def update(self, msg: SBSMessage):
        if self.id != msg.hexIdent:
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
        self.lastSeen = datetime.now()

class TrafficMonitor:

    def __init__(self):
        self.traffic = dict()
        self.cleanup()
    
    def cleanup(self):
        threading.Timer(10, self.cleanup).start()
        now = datetime.now()
        timeout = 20
        for k in list(self.traffic.keys()):
            trafficEntry = self.traffic[k]
            if trafficEntry.lastSeen < now - timedelta(seconds=timeout):
                logger.info("remove traffic {id} which was unseen for longer than {sec} seconds".format(id=trafficEntry.id, sec=timeout))
                del self.traffic[k]


    def update(self, msg: SBSMessage):
        if msg.hexIdent in self.traffic:
            self.traffic[msg.hexIdent].update(msg)
        else:
            logger.info("add new traffic entry {id}".format(id=msg.hexIdent))
            self.traffic[msg.hexIdent] = TrafficEntry(msg.hexIdent, None, msg.latitude, msg.longitude, msg.altitude, msg.track, msg.groundSpeed)

