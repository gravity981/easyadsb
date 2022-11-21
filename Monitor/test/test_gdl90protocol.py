
from Monitor.app.GDL90Protocol import *

def toHexStr(raw: bytes) -> str:
    return ''.join('\\x{:02x}'.format(x) for x in raw)

def test_HeartbeatMessage_wellformed():
    msg = GDL90HeartBeatMessage(uplinkMsgCount=4, basicAndLongMsgCount=567, time=54502)
    enc = encodeHeartbeatMessage(msg)
    expected = b'\x7e\x00\x81\x00\xe6\xd4\x22\x37\x56\xb8\x7e'
    assert enc == expected

def test_TrafficMessage_wellformed():
    msg2 = GDL90TrafficMessage(
        status=GDL90TrafficAlertStatus.No_Alert,
        addrType=GDL90AddressType.ADSB_with_ICAO_addr,
        address=0xAB4549,
        latitude=44.90708, 
        longitude=-122.99488, 
        altitude=5000,
        trackIndicator=GDL90MiscellaneousIndicatorTrack.tt_true_track_angle,
        airborneIndicator=GDL90MiscellaneousIndicatorAirborne.airborne,
        reportIndicator=GDL90MiscellaneousIndicatorReport.updated,
        navIntegrityCat=10,
        navAccuracyCat=9,
        hVelocity=123,
        trackHeading=45, 
        vVelocity=64,
        callsign="N825V",
        emitterCat=GDL90EmitterCategory.light,
        emergencyCode=GDL90EmergencyCode.no_emergency)
    expected = b'\x7e\x14\x00\xAB\x45\x49\x1F\xEF\x15\xA8\x89\x78\x0f\x09\xA9\x07\xb0\x01\x20\x01\x4e\x38\x32\x35\x56\x20\x20\x20\x00\x57\xd6\x7e'
    enc = encodeTrafficMessage(msg2)
    assert enc == expected

def test_OwnshipGeoAltitudeMessage_wellformed():
    msg3 = GDL90OwnshipGeoAltitudeMessage(
        altitude=3280,
        merit=50,
        isWarning=False)
    enc = encodeOwnshipAltitudeMessage(msg3)
    expected = b'\x7E\x0B\x02\x90\x00\x32\x18\x15\x7E'
    assert enc == expected

def test_OnwshipMessage_wellformed():
    msg4 = GDL90TrafficMessage(
        status=GDL90TrafficAlertStatus.No_Alert,
        addrType=GDL90AddressType.ADSB_with_ICAO_addr,
        address=0,
        latitude=49.99999999986941, 
        longitude=8.000522948457947, 
        altitude=3280,
        trackIndicator=GDL90MiscellaneousIndicatorTrack.tt_true_track_angle,
        airborneIndicator=GDL90MiscellaneousIndicatorAirborne.airborne,
        reportIndicator=GDL90MiscellaneousIndicatorReport.updated,
        navIntegrityCat=8,
        navAccuracyCat=9,
        hVelocity=80,
        trackHeading=90, 
        vVelocity=0,
        callsign="D-EZAA",
        emitterCat=GDL90EmitterCategory.light,
        emergencyCode=GDL90EmergencyCode.no_emergency)
    expected = b'\x7E\x0A\x00\x00\x00\x00\x23\x8E\x38\x05\xB0\x73\x0A\xB9\x89\x05\x00\x00\x40\x01\x44\x2D\x45\x5A\x41\x41\x20\x20\x00\x37\x22\x7E'
    enc = encodeOwnshipMessage(msg4)
    assert enc == expected

#msg5 = GDL90TrafficMessage(
#    status=GDL90TrafficAlertStatus.No_Alert,
#    addrType=GDL90AddressType.ADSB_with_ICAO_addr,
#    address=0xAA5506,
#    latitude=46.912222, 
#    longitude=7.499167, 
#    altitude=2000,
#    trackIndicator=GDL90MiscellaneousIndicatorTrack.tt_true_track_angle,
#    airborneIndicator=GDL90MiscellaneousIndicatorAirborne.airborne,
#    reportIndicator=GDL90MiscellaneousIndicatorReport.updated,
#    navIntegrityCat=10,
#    navAccuracyCat=9,
#    hVelocity=123,
#    trackHeading=45, 
#    vVelocity=64,
#    callsign="N825V",
#    emitterCat=GDL90EmitterCategory.light,
#    emergencyCode=GDL90EmergencyCode.no_emergency)