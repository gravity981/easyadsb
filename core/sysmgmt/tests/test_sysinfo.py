import sysmgmt.app.sysinfo as sysinfo


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
    assert 5 == len(tokens)
    assert "PanicAtTheDisco" == tokens["ssid"]
    assert 2.437 == tokens["frequency"]
    assert "06:63:D3:77:91:F0" == tokens["accesspoint"]
    assert 0.857 == tokens["linkQuality"]
    assert -36 == tokens["signalLevel"]


def test_parseIwConfigDisconnected():
    iwconfigStr = """wlan0     IEEE 802.11  ESSID:off/any  
          Mode:Managed  Access Point: Not-Associated   Tx-Power=31 dBm   
          Retry short limit:7   RTS thr:off   Fragment thr:off
          Power Management:on"""
    tokens = sysinfo.Wifi.parseIwConfig(iwconfigStr)
    assert 5 == len(tokens)
    assert tokens["ssid"] is None
    assert tokens["frequency"] is None
    assert tokens["accesspoint"] == "Not-Associated"
    assert tokens["linkQuality"] is None
    assert tokens["signalLevel"] is None


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
    assert 5 == len(tokens)
    assert tokens["ssid"] is None
    assert tokens["frequency"] is None
    assert tokens["accesspoint"] == "06:63:D3:77:91:F0"
    assert tokens["linkQuality"] is None
    assert tokens["signalLevel"] is None


def test_parseIwlistWelformed():
    iwlistStr = """-           Cell 01 - Address: 96:AE:10:E1:03:CC
                    Frequency:2.437 GHz (Channel 6)
                    Quality=57/70  Signal level=-53 dBm
                    Encryption key:on
                    ESSID:"PanicAtTheDisco"
          Cell 02 - Address: 8C:19:B5:B1:63:99
                    Frequency:2.437 GHz (Channel 6)
                    Quality=49/70  Signal level=-61 dBm
                    Encryption key:on
                    ESSID:"Salt_2GHz_B16397"
          Cell 03 - Address: 96:AE:10:E1:03:CC
                    Frequency:2.437 GHz (Channel 6)
                    Quality=60/70  Signal level=-50 dBm
                    Encryption key:on
                    ESSID:"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
          Cell 04 - Address: 74:DA:38:45:37:0A
                    Frequency:2.417 GHz (Channel 2)
                    Quality=42/70  Signal level=-68 dBm
                    Encryption key:on
                    ESSID:"edimax_2.4G_45370A"
          Cell 05 - Address: 8C:19:B5:B1:63:98
                    Frequency:5.26 GHz (Channel 52)
                    Quality=27/70  Signal level=-83 dBm
                    Encryption key:on
                    ESSID:"Salt_5GHz_B16397"
          Cell 06 - Address: 72:19:B5:B1:63:9A
                    Frequency:5.26 GHz (Channel 52)
                    Quality=27/70  Signal level=-83 dBm
                    Encryption key:on
                    ESSID:"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
          Cell 07 - Address: 62:19:B5:B1:63:9B
                    Frequency:2.437 GHz (Channel 6)
                    Quality=48/70  Signal level=-62 dBm
                    Encryption key:on
                    ESSID:"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        """
    wifilist = sysinfo.Wifi.parseIwList(iwlistStr)
    assert len(wifilist) == 7
    first = wifilist[0]
    assert first["ssid"] == "PanicAtTheDisco"
    assert first["frequency"] == 2.437
    assert first["accesspoint"] == "96:AE:10:E1:03:CC"
    assert first["linkQuality"] == 0.814
    assert first["signalLevel"] == -53.0
    assert first["encrypted"] is True


def test_parseIwlistInvalidString():
    iwlistStr = """wlan0     Interface doesn't support scanning."""
    wifilist = sysinfo.Wifi.parseIwList(iwlistStr)
    assert len(wifilist) == 0


def test_parseWpaSupplicantConfWellformed():
    wpaSupplicantStr = """ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
        update_config=1
        country=CH

        network={
                ssid="TestSSID"
                psk="Test123"
        }"""
    wpaSupConf = sysinfo.Wifi.parseWpaSupplicantConf(wpaSupplicantStr)
    assert "ctrl_interface" in wpaSupConf
    assert "update_config" in wpaSupConf
    assert "country" in wpaSupConf
    assert "networks" in wpaSupConf
    assert wpaSupConf["country"] == "CH"
    assert len(wpaSupConf["networks"]) == 1
    assert "ssid" in wpaSupConf["networks"][0]
    assert "psk" in wpaSupConf["networks"][0]


def test_writeWpaSupplicantConfToString():
    referenceStr = (
        "# autogenerated config by easyadsb sysmgmt\n"
        "ctrl_interface=dummy ctrl str\n"
        "update_config=0\n"
        "country=CH\n"
        "network={\n"
        "\tssid=\"dummy_ssid\"\n"
        "\tpsk=passwordhash123\n"
        "}\n"
    )
    wpaSupConf = {
        "ctrl_interface": "dummy ctrl str",
        "update_config": 0,
        "country": "CH",
        "networks": [
            {
                "ssid": "dummy_ssid",
                "psk": "passwordhash123"
            }
        ]
    }
    wpaSupConfStr = sysinfo.Wifi.wpaSupplicantConfToStr(wpaSupConf)
    assert wpaSupConfStr == referenceStr


def test_parseMemInfoWellformed():
    meminfoList = [
        "MemTotal:        1917292 kB",
        "MemFree:          567356 kB",
        "MemAvailable:    1155448 kB",
        "Buffers:           69816 kB",
        "Cached:           526020 kB",
        "SwapCached:            0 kB",
        "Active:           238264 kB",
        "Inactive:         977668 kB",
        "Active(anon):       1496 kB",
        "Inactive(anon):   578716 kB",
        "Active(file):     236768 kB",
        "Inactive(file):   398952 kB",
        "Unevictable:        3012 kB",
        "Mlocked:              16 kB",
        "HighTotal:       1232896 kB",
        "HighFree:          64344 kB",
        "LowTotal:         684396 kB",
        "LowFree:          503012 kB",
        "SwapTotal:        102396 kB",
        "SwapFree:         102396 kB",
        "Dirty:               400 kB",
        "Writeback:             0 kB",
        "AnonPages:        623116 kB",
        "Mapped:           217768 kB",
        "Shmem:              5736 kB",
        "KReclaimable:      51048 kB",
        "Slab:              73744 kB",
        "SReclaimable:      51048 kB",
        "SUnreclaim:        22696 kB",
        "KernelStack:        3096 kB",
        "PageTables:         8384 kB",
        "NFS_Unstable:          0 kB",
        "Bounce:                0 kB",
        "WritebackTmp:          0 kB",
        "CommitLimit:     1061040 kB",
        "Committed_AS:    1543004 kB",
        "VmallocTotal:     245760 kB",
        "VmallocUsed:        6396 kB",
        "VmallocChunk:          0 kB",
        "Percpu:              544 kB",
        "CmaTotal:         327680 kB",
        "CmaFree:          314548 kB",
    ]
    memInfo = sysinfo.Resources.parseMemInfo(meminfoList)
    assert 3 == len(memInfo)
    assert 1917292 == memInfo["memTotal"]
    assert 567356 == memInfo["memFree"]
    assert 0 == memInfo["swapCached"]


def test_parseMemInfoMissingEntries():
    meminfoList = [
        "MemTotal:        1917292 kB",
        "SwapCached:            0 kB",
    ]
    memInfo = sysinfo.Resources.parseMemInfo(meminfoList)
    assert 3 == len(memInfo)
    assert 1917292 == memInfo["memTotal"]
    assert memInfo["memFree"] is None
    assert 0 == memInfo["swapCached"]


def test_parseMemInfoMalformed():
    meminfoList = ["MemTotal:        1917A292 kB", "SwapCached:            0:", "MemFree"]
    memInfo = sysinfo.Resources.parseMemInfo(meminfoList)
    assert 3 == len(memInfo)
    assert memInfo["memTotal"] is None
    assert memInfo["memFree"] is None
    assert memInfo["swapCached"] is None


def test_parseCpuTempWellformed():
    temperature = sysinfo.Resources.parseCpuTemperature("68166")
    assert 68.166 == temperature


def test_parseCpuTempMalformed():
    temperature = sysinfo.Resources.parseCpuTemperature("banana")
    assert temperature is None

