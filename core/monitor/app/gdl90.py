from enum import IntFlag
import logging as log
import math
import queue
import threading
import socket
import ipaddress
import fcntl
import struct
import time

"""
GDL90 protocol implementation based on:
https://www.faa.gov/air_traffic/technology/adsb/archival/media/GDL90_Public_ICD_RevA.PDF
"""


class GDL90Error(Exception):
    pass


class GDL90MessageId(IntFlag):
    Heartbeat = 0
    Initialization = 2
    UplinkData = 7
    HeightAboveTerrain = 9
    OwnshipReport = 10
    OwnshipGeometricAltitude = 11
    TrafficReport = 20
    BasicReport = 30
    LongReport = 31


class GDL90StatusByte1(IntFlag):
    # GDL90 is initialized
    UAT_Initialized = 0x1
    # Reserved
    Reserved = 0x2
    # ATC Services talkback
    RATCS = 0x4
    # GPS Battery low voltage
    GPS_Batt_Low = 0x8
    # Address type talkback
    Addr_Type = 0x10
    # IDENT talkback
    IDENT = 0x20
    # GDL90 Maintenance required
    Maint_Reqd = 0x40
    # Position available for ADS-B Tx
    GPS_Pos_Valid = 0x80


class GDL90StatusByte2(IntFlag):
    # UTC timing is valid
    UTC_OK = 0x1
    # reserved
    Reserved1 = 0x2
    # reserved
    Reserved2 = 0x4
    # reserved
    Reserved3 = 0x8
    # reserved
    Reserved4 = 0x10
    # CSA is not available at this time
    CSA_Not_Available = 0x20
    # CSA has been requested
    CSA_Requested = 0x40
    # Seconds since 0000Z, bit 16
    Timestamp_MS_bit = 0x80


class GDL90TrafficAlertStatus(IntFlag):
    No_Alert = 0
    Traffic_Alert = 1


class GDL90AddressType(IntFlag):
    ADSB_with_ICAO_addr = 0
    ADSB_with_selfassigned_addr = 1
    TISB_with_ICAO_addr = 2
    TISB_with_trk_file_ID = 3
    Surface_Vehicle = 4
    Ground_Station_Beacon = 5


class GDL90MiscellaneousIndicatorTrack(IntFlag):
    tt_not_valid = 0x0
    tt_true_track_angle = 0x1
    tt_heading_magnetic = 0x2
    tt_heading_true = 0x3


class GDL90MiscellaneousIndicatorReport(IntFlag):
    updated = 0x0
    extrapolated = 0x4


class GDL90MiscellaneousIndicatorAirborne(IntFlag):
    on_ground = 0x0
    airborne = 0x8


class GDL90EmitterCategory(IntFlag):
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


class GDL90EmergencyCode(IntFlag):
    no_emergency = 0
    general_emergency = 1
    medical_emergency = 2
    minimum_fuel = 3
    no_communication = 4
    unlawful_interference = 5
    downed_aircraft = 6
    # reserved 7 to 15


class GDL90HeartBeatMessage:
    def __init__(
        self,
        posValid: bool = True,
        isInitialized: bool = True,
        isLowBattery: bool = False,
        time: int = 0,  # seconds since 0000Z (UTC midnight)
        uplinkMsgCount: int = 0,  # 0 to max 31
        basicAndLongMsgCount: int = 0,  # 0 to max 1023
    ):
        self.posValid = posValid
        self.isInitialized = isInitialized
        self.isLowBattery = isLowBattery
        self.time = time
        self.uplinkMsgCount = uplinkMsgCount
        self.basicAndLongMsgCount = basicAndLongMsgCount


class GDL90TrafficMessage:
    def __init__(
        self,
        status: GDL90TrafficAlertStatus = GDL90TrafficAlertStatus.No_Alert,
        addrType: GDL90AddressType = GDL90AddressType.ADSB_with_ICAO_addr,
        address: int = 0x000000,  # 3 byte transponder id
        latitude: float = 0.0,  # +/- 90.0° where + is N and - is S
        longitude: float = 0.0,  # +/- 180.0° where + is E and - is W
        altitude: int = 0,  # -1'000 to 101'350 ft (referenced to 29.92 inches Hg)
        trackIndicator: GDL90MiscellaneousIndicatorTrack = GDL90MiscellaneousIndicatorTrack.tt_not_valid,
        reportIndicator: GDL90MiscellaneousIndicatorReport = GDL90MiscellaneousIndicatorReport.updated,
        airborneIndicator: GDL90MiscellaneousIndicatorAirborne = GDL90MiscellaneousIndicatorAirborne.on_ground,
        navIntegrityCat: int = 0,  # 0 to 11 where 11 is best and 0 worst
        navAccuracyCat: int = 0,  # 0 to 11 where 11 is best and 0 worst
        hVelocity: int = 0,  # unsigned 12 bit, kt
        vVelocity: int = 0,  # signed 12 bit, ftm
        trackHeading: int = 0,  # 0° to 360°
        emitterCat: GDL90EmitterCategory = GDL90EmitterCategory.no_info,
        callsign: str = "",  # max 8 characters long
        emergencyCode: GDL90EmergencyCode = GDL90EmergencyCode.no_emergency,
    ):
        self.status = status
        self.addrType = addrType
        self.address = address
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.trackIndicator = trackIndicator
        self.reportIndicator = reportIndicator
        self.airborneIndicator = airborneIndicator
        self.navIntegrityCat = navIntegrityCat
        self.navAccuracyCat = navAccuracyCat
        self.hVelocity = hVelocity
        self.vVelocity = vVelocity
        self.trackHeading = trackHeading
        self.emitterCat = emitterCat
        self.callsign = callsign
        self.emergencyCode = emergencyCode


class GDL90OwnshipMessage(GDL90TrafficMessage):
    """
    The same as a `GDL90TrafficMessage` but encoded differently
    """

    pass


class GDL90OwnshipGeoAltitudeMessage:
    def __init__(
        self, altitude: int, merit: int, isWarning: bool  # ft  # VFOM, vertical figure of merit (navigation accuracy)
    ):  # true is set, indicates position alarm or fault)
        self.altitude = altitude
        self.merit = merit
        self.isWarning = isWarning


class GDL90Port:
    """
    Used to manage UDP broadcast socket for GDL90 messages.
    Can enqueue messages for sending.
    Performs socket health check and recreates socket automatically on network failure
    """

    EVENT_INIT_COMPLETE = 0
    EVENT_RECEIVE_FAILURE = 1

    STATE_INACTIVE = 0
    STATE_ACTIVE = 1

    def __init__(self, nic: str, port: int, queueSize: int = 1000):
        self._socket = None
        self._nic = nic
        self._port = port
        self._ip = None
        self._netMask = None
        self._broadcastIp = None
        self._sendThread = None
        self._recvThread = None
        self._initThread = None
        self._msgQueue = queue.Queue(maxsize=queueSize)
        self._eventQueue = queue.Queue(maxsize=3)
        self._state = GDL90Port.STATE_INACTIVE
        self._stopFlag = threading.Event()
        self._initFailureReported = False

    @property
    def isActive(self) -> bool:
        """
        Returns whether the GDL90 port is actively sending messages or not
        """
        return self._state == GDL90Port.STATE_ACTIVE

    @property
    def nic(self):
        """
        Returns the name of the network interface in use
        """
        return self._nic

    @property
    def port(self) -> int:
        """
        Returns the port to which gdl90 messages are sent to.
        """
        return self._port

    @property
    def ip(self) -> str:
        """
        Returns the nic's ip address. can be none
        """
        if self.isActive:
            return self._ip

    @property
    def netMask(self) -> str:
        """
        Returns the nic's net mask. can be none
        """
        if self.isActive:
            return self._netMask

    @property
    def broadcastIp(self) -> str:
        """
        Returns the broadcast ip to which gdl90 messages are sent to. can be none
        """
        if self.isActive:
            return self._broadcastIp

    def putMessage(self, msg):
        """
        put a message to send on the queue. this will throw away the message if the queue is full
        """
        try:
            self._msgQueue.put(msg, block=False)
        except queue.Full:
            log.error("gdl90 send queue full (maxsize={}), drop message".format(self._msgQueue.maxsize))

    def exec(self):
        """
        executes the gdl90 port, blocking function
        """
        self._initThread = threading.Thread(target=self._initSocket, name="GDL90SocketInitializer")
        self._initThread.start()
        while True:
            event = self._eventQueue.get()
            if self._state == GDL90Port.STATE_INACTIVE:
                if event == GDL90Port.EVENT_INIT_COMPLETE:
                    self._state = GDL90Port.STATE_ACTIVE
                    log.info("entered active state")
                    self._stopFlag.clear()
                    self._initThread.join()
                    self._sendThread = threading.Thread(target=self._send, name="GDL90Sender")
                    self._recvThread = threading.Thread(target=self._recv, name="GDL90Receiver")
                    self._sendThread.start()
                    self._recvThread.start()
            elif self._state == GDL90Port.STATE_ACTIVE:
                if event == GDL90Port.EVENT_RECEIVE_FAILURE:
                    self._state = GDL90Port.STATE_INACTIVE
                    log.info("entered inactive state")
                    self._stopFlag.set()
                    self._sendThread.join()
                    self._recvThread.join()
                    self._initThread = threading.Thread(target=self._initSocket, name="GDL90SocketInitializer")
                    self._initThread.start()
            self._eventQueue.task_done()

    def _getIpAddress(self, ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ifAddr = 0x8915  # SIOCGIFADDR
        ifNetask = 0x891B  # SIOCGIFNETMASK
        ip = socket.inet_ntoa(fcntl.ioctl(s.fileno(), ifAddr, struct.pack("256s", ifname.encode("UTF-8")))[20:24])
        mask = socket.inet_ntoa(fcntl.ioctl(s.fileno(), ifNetask, struct.pack("256s", ifname.encode("UTF-8")))[20:24])
        return (ip, mask)

    def _initSocket(self):
        while True:
            try:
                self._ip, self._netMask = self._getIpAddress(self._nic)
                addrObj = self._ip + "/" + self._netMask
                net = ipaddress.IPv4Network(self._ip + "/" + self._netMask, False)
                self._broadcastIp = str(net.broadcast_address)
                self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                self._socket.settimeout(2)
                # bind the socket to readback broadcast packages for health check purposes
                self._socket.bind((self._broadcastIp, self._port))
                self._eventQueue.put(GDL90Port.EVENT_INIT_COMPLETE)
                log.info("send gdl90 messages to {} (iface: {}, ip: {})".format(self._broadcastIp, self._nic, addrObj))
                self._initFailureReported = False
                break
            except OSError as ex:
                if not self._initFailureReported:
                    log.error("gdl90 udp socket init failure, {}".format(str(ex)))
                    self._initFailureReported = True
                time.sleep(5)

    def _send(self):
        """
        Get messages from queue and send them to udp address.
        Uses a lock to make sure socket is not modified while sending.
        """
        while True:
            try:
                msg = self._msgQueue.get(timeout=3)
                if type(msg) == GDL90HeartBeatMessage:
                    bytes = encodeHeartbeatMessage(msg)
                elif type(msg) == GDL90TrafficMessage:
                    bytes = encodeTrafficMessage(msg)
                elif type(msg) == GDL90OwnshipMessage:
                    bytes = encodeOwnshipMessage(msg)
                elif type(msg) == GDL90OwnshipGeoAltitudeMessage:
                    bytes = encodeOwnshipAltitudeMessage(msg)
                else:
                    raise TypeError("msg has unexpected type {}".format(type(msg)))
                self._socket.sendto(bytes, self._socket.getsockname())
                self._msgQueue.task_done()
            except queue.Empty:
                pass
            except Exception as e:
                log.error("error sending gdl90 message, {}".format(str(e)))
            finally:
                if self._stopFlag.isSet():
                    break

    def _recv(self):
        """
        Continously read back broadcast data and check for socket timeout.
        Timeout indicates that socket does not work anymore and has to be recreated.
        """
        while True:
            try:
                # returns up to N bytes, can return less, is blocking if there is no data to read from the socket,
                # could be made non-blocking (beware of exceptions in this case)
                data = self._socket.recv(1000)
                if len(data) <= 0:
                    raise ValueError('received unexpected "{}" number of bytes'.format(len(data)))
            except (TimeoutError, ValueError, AttributeError) as e:
                log.error('detected problem with socket "{}", recreate socket...'.format(str(e)))
                self._eventQueue.put(GDL90Port.EVENT_RECEIVE_FAILURE)
                break


def encodeHeartbeatMessage(msg: GDL90HeartBeatMessage) -> bytes:
    """
    Encode a `GDL90HeartBeatMessage` to a bytes array
    """
    status_byte_1 = 0
    status_byte_2 = 0

    if msg.posValid:
        status_byte_1 |= GDL90StatusByte1.GPS_Pos_Valid
    if msg.isInitialized:
        status_byte_1 |= GDL90StatusByte1.UAT_Initialized
    if msg.isLowBattery:
        status_byte_1 |= GDL90StatusByte1.GPS_Batt_Low

    timestamp = msg.time
    if (timestamp & 0x10000) != 0:
        timestamp &= 0x0FFFF
        status_byte_2 |= GDL90StatusByte2.Timestamp_MS_bit

    enc_count = ((msg.uplinkMsgCount & 0x1F) << 11) | (msg.basicAndLongMsgCount & 0x3FF)

    raw = b"".join(
        [
            GDL90MessageId.Heartbeat.to_bytes(1, "big"),
            status_byte_1.to_bytes(1, "big"),
            status_byte_2.to_bytes(1, "big"),
            timestamp.to_bytes(2, "little"),
            enc_count.to_bytes(2, "big"),
        ]
    )
    return _encode(raw)


def encodeOwnshipMessage(msg: GDL90OwnshipMessage) -> bytes:
    """
    Encode a `GDL90OwnshipMessage` to a bytes array
    """
    return _encodeTrafficMessage(GDL90MessageId.OwnshipReport, msg)


def encodeTrafficMessage(msg: GDL90TrafficMessage) -> bytes:
    """
    Encode a `GDL90TrafficMessage` to a bytes array
    """
    return _encodeTrafficMessage(GDL90MessageId.TrafficReport, msg)


def encodeOwnshipAltitudeMessage(msg: GDL90OwnshipGeoAltitudeMessage) -> bytes:
    """
    Encode a `GDL90OwnshipGeoAltitudeMessage` to a bytes array
    """
    enc_alt = int(msg.altitude / 5) & 0xFFFF
    enc_merit = _encode_merit(msg.merit)
    enc_warn = 0x8000 if msg.isWarning else 0x0000
    raw = b"".join([GDL90MessageId.OwnshipGeometricAltitude.to_bytes(1, "big"), enc_alt.to_bytes(2, "big"), (enc_warn | enc_merit).to_bytes(2, "big")])
    return _encode(raw)


def _crc16(data: bytes):
    """
    CRC-16 (CCITT) implemented with a precomputed lookup table
    """
    # fmt: off
    table = [
        0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50A5, 0x60C6, 0x70E7, 0x8108, 0x9129, 0xA14A, 0xB16B, 0xC18C, 0xD1AD, 0xE1CE, 0xF1EF,
        0x1231, 0x0210, 0x3273, 0x2252, 0x52B5, 0x4294, 0x72F7, 0x62D6, 0x9339, 0x8318, 0xB37B, 0xA35A, 0xD3BD, 0xC39C, 0xF3FF, 0xE3DE,
        0x2462, 0x3443, 0x0420, 0x1401, 0x64E6, 0x74C7, 0x44A4, 0x5485, 0xA56A, 0xB54B, 0x8528, 0x9509, 0xE5EE, 0xF5CF, 0xC5AC, 0xD58D,
        0x3653, 0x2672, 0x1611, 0x0630, 0x76D7, 0x66F6, 0x5695, 0x46B4, 0xB75B, 0xA77A, 0x9719, 0x8738, 0xF7DF, 0xE7FE, 0xD79D, 0xC7BC,
        0x48C4, 0x58E5, 0x6886, 0x78A7, 0x0840, 0x1861, 0x2802, 0x3823, 0xC9CC, 0xD9ED, 0xE98E, 0xF9AF, 0x8948, 0x9969, 0xA90A, 0xB92B,
        0x5AF5, 0x4AD4, 0x7AB7, 0x6A96, 0x1A71, 0x0A50, 0x3A33, 0x2A12, 0xDBFD, 0xCBDC, 0xFBBF, 0xEB9E, 0x9B79, 0x8B58, 0xBB3B, 0xAB1A,
        0x6CA6, 0x7C87, 0x4CE4, 0x5CC5, 0x2C22, 0x3C03, 0x0C60, 0x1C41, 0xEDAE, 0xFD8F, 0xCDEC, 0xDDCD, 0xAD2A, 0xBD0B, 0x8D68, 0x9D49,
        0x7E97, 0x6EB6, 0x5ED5, 0x4EF4, 0x3E13, 0x2E32, 0x1E51, 0x0E70, 0xFF9F, 0xEFBE, 0xDFDD, 0xCFFC, 0xBF1B, 0xAF3A, 0x9F59, 0x8F78,
        0x9188, 0x81A9, 0xB1CA, 0xA1EB, 0xD10C, 0xC12D, 0xF14E, 0xE16F, 0x1080, 0x00A1, 0x30C2, 0x20E3, 0x5004, 0x4025, 0x7046, 0x6067,
        0x83B9, 0x9398, 0xA3FB, 0xB3DA, 0xC33D, 0xD31C, 0xE37F, 0xF35E, 0x02B1, 0x1290, 0x22F3, 0x32D2, 0x4235, 0x5214, 0x6277, 0x7256,
        0xB5EA, 0xA5CB, 0x95A8, 0x8589, 0xF56E, 0xE54F, 0xD52C, 0xC50D, 0x34E2, 0x24C3, 0x14A0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
        0xA7DB, 0xB7FA, 0x8799, 0x97B8, 0xE75F, 0xF77E, 0xC71D, 0xD73C, 0x26D3, 0x36F2, 0x0691, 0x16B0, 0x6657, 0x7676, 0x4615, 0x5634,
        0xD94C, 0xC96D, 0xF90E, 0xE92F, 0x99C8, 0x89E9, 0xB98A, 0xA9AB, 0x5844, 0x4865, 0x7806, 0x6827, 0x18C0, 0x08E1, 0x3882, 0x28A3,
        0xCB7D, 0xDB5C, 0xEB3F, 0xFB1E, 0x8BF9, 0x9BD8, 0xABBB, 0xBB9A, 0x4A75, 0x5A54, 0x6A37, 0x7A16, 0x0AF1, 0x1AD0, 0x2AB3, 0x3A92,
        0xFD2E, 0xED0F, 0xDD6C, 0xCD4D, 0xBDAA, 0xAD8B, 0x9DE8, 0x8DC9, 0x7C26, 0x6C07, 0x5C64, 0x4C45, 0x3CA2, 0x2C83, 0x1CE0, 0x0CC1,
        0xEF1F, 0xFF3E, 0xCF5D, 0xDF7C, 0xAF9B, 0xBFBA, 0x8FD9, 0x9FF8, 0x6E17, 0x7E36, 0x4E55, 0x5E74, 0x2E93, 0x3EB2, 0x0ED1, 0x1EF0
    ]
    # fmt: on

    crc = 0
    for byte in data:
        crc = (crc << 8) ^ table[(crc >> 8)] ^ byte
        crc &= 0xFFFF  # important, crc must stay 16bits all the way through
    result = (crc & 0xFF) << 8 | (crc & 0xFF00) >> 8
    return result


def _addCrc(msg: bytes) -> bytes:
    return b"".join([msg, _crc16(msg).to_bytes(2, "big")])


def _escape(msg: bytes) -> bytes:
    escaped = bytes()
    for b in msg:
        if b == 0x7D or b == 0x7E:
            escaped += b"\x7d"
            escaped += (b ^ 0x20).to_bytes(1, "big")
        else:
            escaped += b.to_bytes(1, "big")
    return escaped


def _encode(msg: bytes) -> bytes:
    msg = _addCrc(msg)
    msg = _escape(msg)
    return b"".join([b"\x7e", msg, b"\x7e"])


def _encode_latlon(latlon: float) -> int:
    latlon = int(latlon * (0x7FFFFF / 180.0))
    if latlon < 0:
        latlon &= 0xFFFFFF
    return latlon


def _encode_altitude(alt: int) -> int:
    return int((alt + 1000) / 25) & 0xFFF


def _encode_miscellaneous(
    trackIndicator: GDL90MiscellaneousIndicatorTrack, reportIndicator: GDL90MiscellaneousIndicatorReport, airborneIndicator: GDL90MiscellaneousIndicatorAirborne
) -> int:
    return trackIndicator | reportIndicator | airborneIndicator


def _encode_hVelocity(velocity: int) -> int:
    if velocity < 0:
        return 0
    elif velocity > 0xFFE:
        return 0xFFE
    return velocity


def _encode_vVelocity(velocity: int) -> int:
    if velocity is None:
        return 0x800
    if velocity > 32576:
        return 0x1FE
    elif velocity < -32576:
        return 0xE02
    else:
        return int(velocity / 64)


def _encode_track(trackHeading: int) -> int:
    if trackHeading < 0 or trackHeading > 360:
        raise GDL90Error("trackHeading out of bounds, must be between 0 and 360 degrees")
    elif trackHeading == 360:
        trackHeading = 0
    return math.floor(trackHeading * 256 / 360.0)


def _encode_callsign(callsign: str) -> str:
    if callsign is None:
        return "".ljust(8)
    return callsign.ljust(8)


def _encode_merit(merit: int) -> int:
    if merit is None:
        return 0x7FFF
    elif merit >= 32766:
        return 0x7FFE
    return merit


def _encodeTrafficMessage(msgId: GDL90MessageId, msg: GDL90TrafficMessage) -> bytes:
    # st aa aa aa ll ll ll nn nn nn dd dm ia hh hv vv tt ee cc cc cc cc cc cc cc cc px
    enc_alt = _encode_altitude(msg.altitude)
    enc_misc = _encode_miscellaneous(msg.trackIndicator, msg.reportIndicator, msg.airborneIndicator)
    enc_hVel = _encode_hVelocity(msg.hVelocity)
    enc_vVel = _encode_vVelocity(msg.vVelocity)
    enc_trk = _encode_track(msg.trackHeading)
    enc_callsign = _encode_callsign(msg.callsign)

    raw = b"".join(
        [
            msgId.to_bytes(1, "big"),
            ((msg.status << 4) | msg.addrType).to_bytes(1, "big"),
            msg.address.to_bytes(3, "big"),
            _encode_latlon(msg.latitude).to_bytes(3, "big"),
            _encode_latlon(msg.longitude).to_bytes(3, "big"),
            ((enc_alt & 0xFF0) >> 4).to_bytes(1, "big"),
            (((enc_alt & 0x00F) << 4) | enc_misc).to_bytes(1, "big"),
            (((msg.navIntegrityCat & 0xF) << 4) | (msg.navAccuracyCat & 0xF)).to_bytes(1, "big"),
            ((enc_hVel & 0xFF0) >> 4).to_bytes(1, "big"),
            (((enc_hVel & 0x00F) << 4) | ((enc_vVel & 0xF00) >> 8)).to_bytes(1, "big"),
            (enc_vVel & 0x0FF).to_bytes(1, "big"),
            enc_trk.to_bytes(1, "big"),
            msg.emitterCat.to_bytes(1, "big"),
            enc_callsign.encode("utf-8"),
            (msg.emergencyCode << 4).to_bytes(1, "big"),
        ]
    )
    return _encode(raw)
