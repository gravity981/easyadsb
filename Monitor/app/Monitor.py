from enum import Enum
from SBSProtocol import SBSMessage
from datetime import datetime, timedelta
import threading
import logging
import json
from pynmeagps import NMEAMessage

logger = logging.getLogger("logger")

class GPSStatus(Enum):
    Active = 1
    Void = 0

class GpsMonitor:
    def __init__(self):
        pass

    def update(self, msg: NMEAMessage):
        
        # satellite status
        # ID: GSV - GNSS Satellites in View
        # <NMEA(GPGSV, numMsg=4, msgNum=1, numSV=14, svid_01=2, elv_01=41.0, az_01=149, cno_01=43, svid_02=6, elv_02=3.0, az_02=26, cno_02=10, svid_03=11, elv_03=27.0, az_03=50, cno_03=43, svid_04=12, elv_04=33.0, az_04=90, cno_04=39)>
        # ID: GSA - GNSS DOP and Active Satellites
        # <NMEA(GPGSA, opMode=A, navMode=3, svid_01=29, svid_02=25, svid_03=12, svid_04=31, svid_05=11, svid_06=2, svid_07=20, svid_08=, svid_09=, svid_10=, svid_11=, svid_12=, PDOP=2.71, HDOP=1.59, VDOP=2.19)>
        
        # useful for monitoring ownship
        # ID: VTG - Course Over Ground and Ground Speed
        # <NMEA(GPVTG, cogt=, cogtUnit=T, cogm=, cogmUnit=M, sogn=0.22, sognUnit=N, sogk=0.408, sogkUnit=K, posMode=A)>
        # ID: GGA - Global Positioning System Fixed Data
        # <NMEA(GPGGA, time=19:57:12, lat=46.9263156667, NS=N, lon=7.4543581667, EW=E, quality=1, numSV=7, HDOP=1.59, alt=578.5, altUnit=M, sep=47.2, sepUnit=M, diffAge=, diffStation=)>
        # ID: RMC - Recommended Minimum Specific GNSS Data
        # <NMEA(GPRMC, time=19:57:12, status=A, lat=46.9263156667, NS=N, lon=7.4543581667, EW=E, spd=0.22, cog=, date=2022-11-20, mv=, mvEW=, posMode=A)>
        
        # probably unused
        # ID: GLL - Geographic Position - Latitude/Longitude
        # <NMEA(GPGLL, lat=46.9263158333, NS=N, lon=7.4543563333, EW=E, time=19:57:11, status=A, posMode=A)>
        return

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
        self.status=status
        self.utc=utc
        self.latitude=latitude
        self.longitude=longitude
        self.groundSpeed=groundSpeed
        self.track=track
        self.date=date
        self.magneticVariation=magneticVariation

class Satellite:
    def __init__(self,
        prnNumber,
        elevation,
        azimuth,
        snr):
        self.prnNumber=prnNumber
        self.elevation=elevation
        self.azimuth=azimuth
        self.snr=snr

class SatellitesMonitor:
    def __init__(self,
        satellitesVisible: int,
        satellitesInUse: int):
        self.satellitesVisible=satellitesVisible
        self.satellitesInUse=satellitesInUse


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

    def __init__(self):
        self.traffic = dict()
        with open('/home/data/aircrafts.json') as json_file:
            self.aircrafts_db = json.load(json_file)
        with open('/home/data/models.json') as json_file:
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
            

