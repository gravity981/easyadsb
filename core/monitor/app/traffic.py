from enum import IntEnum
from datetime import datetime
import threading
import logging
import json
from copy import deepcopy

try:
    from monitor.app.sbs import SBSMessage
except ImportError:
    from sbs import SBSMessage

logger = logging.getLogger("logger")


class TrafficError(Exception):
    pass


class TrafficCategory(IntEnum):
    """
    Traffic Category, defined by GDL90
    - no_info = 0
    - light = 1, < 15'500 lbs (7'030 kg)
    - small = 2, 15'500 lbs < x < 75'000 lbs (34'019 kg)
    - large = 3, 75'000 lbs < x < 300'000 lbs (136'077 kg)
    - high_vortex_large = 4
    - heavy = 5
    - highly_maneuverable = 6
    - rotorcraft = 7
    - glider = 9
    - lighter_than_air = 10
    - sky_diver = 11
    - paraglider = 12
    - unmanned = 14
    - spaceship = 15
    - surface_vehicle_emergency = 17
    - surface_vehicle_service = 18
    - point_obstacle = 19
    - cluster_obstacle = 20
    - line_obstacle = 21

    """

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


class TrafficEntry(dict):
    """TrafficEntry"""

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
        groundSpeed: int,
        verticalSpeed: int,
        squawk: int,
        alert: bool,
        emergency: bool,
        spi: bool,
        isOnGround: bool,
    ):
        """
        Constructor
        """
        self["id"] = int(id, 16)
        self["callsign"] = callsign
        self["model"] = model
        self["category"] = category
        self["latitude"] = latitude
        self["longitude"] = longitude
        self["altitude"] = altitude
        self["track"] = track
        self["groundSpeed"] = groundSpeed
        self["verticalSpeed"] = verticalSpeed
        self["squawk"] = squawk
        self["alert"] = alert
        self["emergency"] = emergency
        self["spi"] = spi
        self["isOnGround"] = isOnGround
        self._lastSeen = datetime.now()
        self["lastSeen"] = self._lastSeen.strftime("%H:%M:%S")
        self["msgCount"] = 1

    @property
    def id(self) -> int:
        """
        Transponder ID
        """
        return self["id"]

    @property
    def callsign(self) -> str:
        """
        Callsign, can be None
        """
        return self["callsign"]

    @property
    def model(self) -> str:
        """
        ICAO Type designator, can be None
        """
        return self["model"]

    @property
    def category(self) -> TrafficCategory:
        """
        See :class:`TrafficCategory`, can be None
        """
        return self["category"]

    @property
    def latitude(self) -> float:
        """
        latitude in the format degrees and (decimal) fraction
        Positive value is considered North, negative South
        can be None
        """
        return self["latitude"]

    @property
    def longitude(self) -> float:
        """
        longitude in the format degrees and (decimal) fraction
        Positive value is considered East, negative West
        can be None
        """
        return self["longitude"]

    @property
    def altitude(self) -> int:
        """
        Altitude above mean sea level in ft (referenced to 29.92 inches Hg)
        """
        return self["altitude"]

    @property
    def track(self) -> int:
        """
        Track in degrees from 0 to 360
        """
        return self["track"]

    @property
    def groundSpeed(self):
        """
        Ground Speed in knots
        """
        return self["groundSpeed"]

    @property
    def verticalSpeed(self):
        """
        Vertical Speed in ft/min
        """
        return self["verticalSpeed"]

    @property
    def squawk(self):
        """
        squawk code
        """
        return self["squawk"]

    @property
    def alert(self):
        """
        indicates that squawk code has changed
        """
        return self["alert"]

    @property
    def emergency(self):
        """
        indicates that emergency squawk code has been set
        """
        return self["emergency"]

    @property
    def spi(self):
        """
        indicates that transponder ident has been activated
        """
        return self["spi"]

    @property
    def isOnGround(self):
        """
        indicates that ground squat switch is active
        """
        return self["isOnGround"]

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
        return self["msgCount"]

    # TODO stop updating with SBSMessage, provide generic update method
    # this is to make this module independent of SBS and allow other sources to update traffic
    def update(self, msg: SBSMessage):
        """
        Update :class:`TrafficEntry` from :class:`SBSMessage`.
        Will raise :class:`TrafficError` on transponder ID mismatch
        """
        if self["id"] != int(msg.hexIdent, 16):
            raise TrafficError("Cannot update traffic entry with mismatching hexIdent")
        if msg.latitude is not None:
            self["latitude"] = msg.latitude
        if msg.longitude is not None:
            self["longitude"] = msg.longitude
        if msg.altitude is not None:
            self["altitude"] = msg.altitude
        if msg.track is not None:
            self["track"] = msg.track
        if msg.groundSpeed is not None:
            self["groundSpeed"] = msg.groundSpeed
        if msg.verticalRate is not None:
            self["verticalSpeed"] = msg.verticalRate
        if msg.squawk is not None:
            self["squawk"] = msg.squawk
        if msg.alert is not None:
            self["alert"] = msg.alert
        if msg.emergency is not None:
            self["emergency"] = msg.emergency
        if msg.spi is not None:
            self["spi"] = msg.spi
        if msg.isOnGround is not None:
            self["isOnGround"] = msg.isOnGround

        self._lastSeen = datetime.utcnow()
        self["lastSeen"] = self._lastSeen.strftime("%H:%M:%S")
        self["msgCount"] += 1

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
            "vSpd={}, "
            "sqwk={}, "
            "alrt={}, "
            "emrg={}, "
            "spi={}, "
            "onGround={}, "
            "lastSeen={:%H:%M:%S}, "
            "msgCount={})>"
        ).format(
            self["id"],
            self["callsign"],
            self["model"],
            self["category"],
            self["latitude"],
            self["longitude"],
            self["altitude"],
            self["track"],
            self["groundSpeed"],
            self["verticalSpeed"],
            self["squawk"],
            self["alert"],
            self["emergency"],
            self["spi"],
            self["isOnGround"],
            self["lastSeen"],
            self["msgCount"],
        )


# TODO make this an observable subject
class TrafficMonitor:
    """
    Monitors Flight Traffic. Can be updated with :class:`SBSMessage`
    """

    def __init__(self, aircraftsDB: json = None, modelsDB: json = None):
        self._traffic = dict()
        self._aircraftsDB = aircraftsDB
        self._modelsDB = modelsDB
        self._lock = threading.Lock()
        self._timer = None
        self._observers = list()

    @property
    def traffic(self) -> dict():
        """
        Dictionary of :class:`TrafficEntry`
        """
        with self._lock:
            return deepcopy(self._traffic)

    def startAutoCleanup(self, interval: int = 10):
        """
        Start cleanup timer, removes unseen traffic
        """
        self._cleanup(interval)

    def stopAutoCleanup(self):
        """
        Stop cleanup timer, removes unseen traffic
        """
        if self._timer is not None:
            self._timer.cancel()

    def register(self, obj):
        """
        Register an observer for `TrafficEntry` updates
        """
        self._observers.append(obj)

    # TODO stop updating with SBSMessage, provide generic update method
    # this is to make this module independent of SBS and allow other sources to update traffic
    def update(self, msg: SBSMessage):
        """
        Update :class:`TrafficMonitor` from :class:`SBSMessage`
        """
        with self._lock:
            if msg.hexIdent in self._traffic:
                entry = self._traffic[msg.hexIdent]
                entry.update(msg)
            else:
                callsign, model = self._aircraftLookUp(msg)
                if callsign is None:
                    callsign = msg.callsign
                category = self._modelLookUp(model)
                entry = TrafficEntry(
                    msg.hexIdent,
                    callsign,
                    model,
                    category,
                    msg.latitude,
                    msg.longitude,
                    msg.altitude,
                    msg.track,
                    msg.groundSpeed,
                    msg.verticalRate,
                    msg.squawk,
                    msg.alert,
                    msg.emergency,
                    msg.spi,
                    msg.isOnGround,
                )
                self._traffic[msg.hexIdent] = entry
                logger.info("add new {:X}, {}, {}, {} (count {})".format(entry.id, entry.callsign, entry.model, entry.category.name, len(self._traffic)))
            self._notify(entry)

    def _notify(self, trafficEntry):
        for obj in self._observers:
            obj.notify(trafficEntry)

    def _cleanup(self, interval: int):
        with self._lock:
            self._timer = threading.Timer(interval, self._cleanup, [interval])
            self._timer.start()
            maxLastSeenSeconds = 300
            for k in list(self._traffic.keys()):
                entry = self._traffic[k]
                if entry.lastSeen > maxLastSeenSeconds:
                    logger.info(
                        "remove {:X}, {}, {}, {} (unseen for >{} seconds)".format(
                            entry.id, entry.callsign, entry.model, entry.category.name, maxLastSeenSeconds
                        )
                    )
                    del self._traffic[k]

    def _aircraftLookUp(self, msg: SBSMessage) -> tuple[str, str]:
        if self._aircraftsDB is not None:
            callsign, model, *_ = self._aircraftsDB[msg.hexIdent] if msg.hexIdent in self._aircraftsDB.keys() else [None, None]
            return (callsign, model)
        else:
            return (None, None)

    def _modelLookUp(self, model: str) -> TrafficCategory:
        if self._modelsDB is not None:
            cat, *_ = self._modelsDB[model] if model in self._modelsDB.keys() else [0]
            return TrafficCategory(cat)
        else:
            return TrafficCategory.no_info
