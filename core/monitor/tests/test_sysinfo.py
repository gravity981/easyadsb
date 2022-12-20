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
    assert "" == tokens["ssid"]
    assert "" == tokens["frequency"]
    assert "Not-Associated" == tokens["accesspoint"]
    assert "" == tokens["linkQuality"]
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
    assert 5 == len(tokens)
    assert "" == tokens["ssid"]
    assert "" == tokens["frequency"]
    assert "06:63:D3:77:91:F0" == tokens["accesspoint"]
    assert "" == tokens["linkQuality"]
    assert "" == tokens["signalLevel"]


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
