import subprocess
import logging as log
import shlex


class Wifi:
    def getIwConfig(iface):
        process = subprocess.run(["iwconfig", iface], capture_output=True, encoding="utf-8")
        return process.stdout

    def parseIwConfig(iwconfigStr) -> dict:
        """
        Returns a dict with following entries
        - SSID: str
        - frequency: float [GHz]
        - accesspoint: str [MAC addr]
        - linkQuality: float [%]
        - signalLevel: float [dBm]
        """
        log.debug(iwconfigStr)
        iwconfig = dict()

        skey = "ESSID:"
        ekey = " "
        ssid = Wifi._extractString(skey, ekey, iwconfigStr)
        iwconfig["ssid"] = Wifi._parseSsid(ssid)

        skey = "Frequency:"
        ekey = " GHz"
        frequency = Wifi._extractString(skey, ekey, iwconfigStr)
        iwconfig["frequency"] = Wifi._parseFrequency(frequency)

        skey = "Access Point:"
        ekey = "  "
        ap = Wifi._extractString(skey, ekey, iwconfigStr)
        iwconfig["accesspoint"] = Wifi._parseAccesspoint(ap)

        skey = "Link Quality="
        ekey = " "
        linkQuality = Wifi._extractString(skey, ekey, iwconfigStr)
        iwconfig["linkQuality"] = Wifi._parseLinkQuality(linkQuality)

        skey = "Signal level="
        ekey = " dBm"
        signalLevel = Wifi._extractString(skey, ekey, iwconfigStr)
        iwconfig["signalLevel"] = Wifi._parseSignalLevel(signalLevel)

        return iwconfig

    def getIwList(iface):
        cmd = "awk '/ESSID/ || /Frequency/ || /Cell/ || /Quality/ || /Address/ || /Encryption/'"
        pAwk = subprocess.Popen(shlex.split(cmd), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        cmd = "iwlist {} scan".format(iface)
        pIwlist = subprocess.Popen(shlex.split(cmd), stdout=pAwk.stdin)
        out, err = pAwk.communicate()
        pIwlist.wait()
        return out.decode("utf-8")

    def parseIwList(iwlistStr):
        """
        returns a list of dicts with following entries
        - SSID: str
        - frequency: float [GHz]
        - accesspoint: str [MAC addr]
        - linkQuality: float [%]
        - signalLevel: float [dBm]
        - encrypted: bool
        """
        wifilist = []
        cells = iwlistStr.replace("\n", " ").split("Cell")
        if len(cells) > 1:
            del cells[0]
        else:
            return wifilist
        for cell in cells:
            info = dict()

            skey = "ESSID:"
            ekey = " "
            val = Wifi._extractString(skey, ekey, cell)
            info["ssid"] = Wifi._parseSsid(val)

            skey = "Address: "
            ekey = " "
            val = Wifi._extractString(skey, ekey, cell)
            info["accesspoint"] = Wifi._parseAccesspoint(val)

            skey = "Frequency:"
            ekey = " "
            val = Wifi._extractString(skey, ekey, cell)
            info["frequency"] = Wifi._parseFrequency(val)

            skey = "Quality="
            ekey = " "
            val = Wifi._extractString(skey, ekey, cell)
            info["linkQuality"] = Wifi._parseLinkQuality(val)

            skey = "Signal level="
            ekey = " "
            val = Wifi._extractString(skey, ekey, cell)
            info["signalLevel"] = Wifi._parseSignalLevel(val)

            skey = "Encryption key:"
            ekey = " "
            val = Wifi._extractString(skey, ekey, cell)
            info["encrypted"] = Wifi._parseEncrypted(val)

            wifilist.append(info)
        return wifilist

    def _extractString(skey, ekey, raw):
        """
        returns the substring from raw between skey and ekey
        """
        start = raw.find(skey)
        if start < 0:
            return
        start += len(skey)
        end = raw.find(ekey, start)
        if end < 0:
            return
        return raw[start:end]

    def _parseSsid(ssid):
        if ssid and '"' in ssid:
            ssid = ssid.strip('"')
        else:
            ssid = None
        return ssid

    def _parseFrequency(frequency):
        if frequency:
            try:
                frequency = float(frequency)
            except ValueError:
                frequency = None
        else:
            frequency = None
        return frequency

    def _parseAccesspoint(ap):
        if ap:
            ap = ap.strip()
        else:
            ap = None
        return ap

    def _parseLinkQuality(linkQuality):
        if linkQuality:
            linkQuality = linkQuality.split("/")
            if len(linkQuality) == 2:
                try:
                    linkQuality = round(float(linkQuality[0]) / float(linkQuality[1]), 3)
                except ValueError:
                    linkQuality = None
            else:
                linkQuality = None
        else:
            linkQuality = None
        return linkQuality

    def _parseSignalLevel(signalLevel):
        if signalLevel:
            try:
                signalLevel = float(signalLevel)
            except ValueError:
                signalLevel = None
        else:
            signalLevel = None
        return signalLevel

    def _parseEncrypted(encrypted):
        if encrypted:
            encrypted = encrypted.strip()
        else:
            encrypted = None
        return encrypted == "on"


class Resources:

    def getCpuTempFromSysfs():
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return f.read()

    def parseCpuTemperature(milliCelsius: str) -> float:
        """
        Returns CPU temperature in °C from milliCelsius string
        """
        log.debug(milliCelsius)
        try:
            return float(milliCelsius) / 1000
        except ValueError:
            return None

    def getMemInfoFromProcfs():
        with open("/proc/meminfo") as f:
            return f.readlines()

    def parseMemInfo(meminfo: list) -> dict:
        """
        Returns a dict with the following entries from a meminfo list of strings
        - memTotal: float [kB] (total usable RAM)
        - memFree: float [kB] (free RAM, the memory which is not used for anything at all)
        - swapCached: float [kB] (recently used swap memory, which increases the speed of I/O)
        """
        log.debug(meminfo)
        result = {"memTotal": None, "memFree": None, "swapCached": None}
        for i in meminfo:
            if "MemTotal" in i:
                result["memTotal"] = Resources._getMemInfoValue(i)
            elif "MemFree" in i:
                result["memFree"] = Resources._getMemInfoValue(i)
            elif "SwapCached" in i:
                result["swapCached"] = Resources._getMemInfoValue(i)
        return result

    def getStatFromProcfs() -> float:
        with open("/proc/stat") as f:
            return f.readlines()

    def parseCpuUsage(stat: str) -> float:
        """
        not available, should return an average cpu usage over the past couple minutes
        """
        log.debug(stat)
        # todo parse stat string, (requires calculation over time)
        return 0.0

    def _getMemInfoValue(raw) -> float:
        # e.g. "MemTotal:        1917292 kB" returns 1917292
        try:
            return int(raw.split(":")[-1].strip().split()[0])
        except (ValueError, IndexError):
            return None
