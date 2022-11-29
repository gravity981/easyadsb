import monitor.app.traffic as traffic
import monitor.app.sbs as sbs


def test_updateTrafficMonitor():
    monitor = traffic.TrafficMonitor()
    msg = sbs.SBSMessage(hexIdent="AABBCC", callsign="ABCDEFGH")
    monitor.update(msg)
    assert "AABBCC" in monitor.traffic.keys()
    assert "ABCDEFGH" == monitor.traffic["AABBCC"].callsign
