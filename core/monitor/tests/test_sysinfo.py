import monitor.app.sysinfo as sysinfo


def test_parseIwConfigConnected():
    iwconfigStr = """wlan0     IEEE 802.11  ESSID:"PanicAtTheDisco"  
          Mode:Managed  Frequency:2.437 GHz  Access Point: 06:63:D3:77:91:F0   
          Bit Rate=72.2 Mb/s   Tx-Power=31 dBm   
          Retry short limit:7   RTS thr:off   Fragment thr:off
          Power Management:on
          Link Quality=60/70  Signal level=-36 dBm  
          Rx invalid nwid:0  Rx invalid crypt:0  Rx invalid frag:0
          Tx excessive retries:289  Invalid misc:0   Missed beacon:0"""
    tokens = sysinfo.Wifi.parseIwConfig(iwconfigStr)
    assert "ssid" in tokens
    assert "frequency" in tokens
    assert "accesspoint" in tokens
    assert "quality" in tokens
    assert "signalLevel" in tokens
    assert "PanicAtTheDisco" == tokens["ssid"]
    assert 2.437 == tokens["frequency"]
    assert "06:63:D3:77:91:F0" == tokens["accesspoint"]
    assert 0.857 == tokens["quality"]
    assert -36 == tokens["signalLevel"]


def test_parseIwConfigDisconnected():
    iwconfigStr = """wlan0     IEEE 802.11  ESSID:off/any  
          Mode:Managed  Access Point: Not-Associated   Tx-Power=31 dBm   
          Retry short limit:7   RTS thr:off   Fragment thr:off
          Power Management:on"""
    tokens = sysinfo.Wifi.parseIwConfig(iwconfigStr)
    assert "ssid" in tokens
    assert "frequency" in tokens
    assert "accesspoint" in tokens
    assert "quality" in tokens
    assert "signalLevel" in tokens
    assert "" == tokens["ssid"]
    assert "" == tokens["frequency"]
    assert "Not-Associated" == tokens["accesspoint"]
    assert "" == tokens["quality"]
    assert "" == tokens["signalLevel"]


def test_parseIwConfigMalformed():
    iwconfigStr = """wlan0     IEEE 802.11  ESSIID:"PanicAtTheDisco"  
          Mode:Managed  Frequency:2.4B37 GHz  Access Point: 06:63:D3:77:91:F0   
          Bit Rate=72.2 Mb/s   Tx-Power=31 dBm   
          Retry short limit:7   RTS thr:off   Fragment thr:off
          Power Management:on
          Link Quality=6070  Signal level=--36 dBm  
          Rx invalid nwid:0  Rx invalid crypt:0  Rx invalid frag:0
          Tx excessive retries:289  Invalid misc:0   Missed beacon:0"""
    tokens = sysinfo.Wifi.parseIwConfig(iwconfigStr)
    assert "ssid" in tokens
    assert "frequency" in tokens
    assert "accesspoint" in tokens
    assert "quality" in tokens
    assert "signalLevel" in tokens
    assert "" == tokens["ssid"]
    assert "" == tokens["frequency"]
    assert "06:63:D3:77:91:F0" == tokens["accesspoint"]
    assert "" == tokens["quality"]
    assert "" == tokens["signalLevel"]
