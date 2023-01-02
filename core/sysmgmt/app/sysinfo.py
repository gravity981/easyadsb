import subprocess
import logging as log
import shlex


def restartDhcpcd():
    cmd = "systemctl restart dhcpcd"
    process = subprocess.run(shlex.split(cmd), capture_output=True, encoding="utf-8")
    if process.stderr:
        log.error(process.stderr)
    else:
        log.info(process.stdout)


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
        ssid = Wifi._extractString("ESSID:", " ", iwconfigStr)
        iwconfig["ssid"] = Wifi._parseSsid(ssid)
        frequency = Wifi._extractString("Frequency:", " GHz", iwconfigStr)
        iwconfig["frequency"] = Wifi._parseFrequency(frequency)
        ap = Wifi._extractString("Access Point:", "  ", iwconfigStr)
        iwconfig["accesspoint"] = Wifi._parseAccesspoint(ap)
        linkQuality = Wifi._extractString("Link Quality=", " ", iwconfigStr)
        iwconfig["linkQuality"] = Wifi._parseLinkQuality(linkQuality)
        signalLevel = Wifi._extractString("Signal level=", " dBm", iwconfigStr)
        iwconfig["signalLevel"] = Wifi._parseSignalLevel(signalLevel)

        return iwconfig

    def getIwList(iface):
        cmd = "awk '/ESSID/ || /Frequency/ || /Cell/ || /Quality/ || /Address/ || /Encryption/'"
        pAwk = subprocess.Popen(shlex.split(cmd), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cmd = "iwlist {} scan".format(iface)
        pIwlist = subprocess.Popen(shlex.split(cmd), stdout=pAwk.stdin, stderr=subprocess.PIPE)
        out, err = pAwk.communicate()
        if err:
            raise ChildProcessError(err)
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
            val = Wifi._extractString("ESSID:", " ", cell)
            info["ssid"] = Wifi._parseSsid(val)
            val = Wifi._extractString("Address: ", " ", cell)
            info["accesspoint"] = Wifi._parseAccesspoint(val)
            val = Wifi._extractString("Frequency:", " ", cell)
            info["frequency"] = Wifi._parseFrequency(val)
            val = Wifi._extractString("Quality=", " ", cell)
            info["linkQuality"] = Wifi._parseLinkQuality(val)
            val = Wifi._extractString("Signal level=", " ", cell)
            info["signalLevel"] = Wifi._parseSignalLevel(val)
            val = Wifi._extractString("Encryption key:", " ", cell)
            info["encrypted"] = Wifi._parseEncrypted(val)

            wifilist.append(info)
        return wifilist

    def getWpaSupplicantConf():
        with open("/etc/wpa_supplicant/wpa_supplicant.conf", "r") as f:
            return f.read()

    def parseWpaSupplicantConf(wpaSupplicantStr):
        """
        returns a dict representing the wpa supplicant configuration.

        currently supported keys:
        - ctrl_interface: str
        - update_config: int
        - country: str
        - networks: list
          - ssid: str
          - psk: str
        """
        wpaSupConf = dict()
        wpaSupStrFiltered = Wifi._filterComments(wpaSupplicantStr)
        val = Wifi._extractString("ctrl_interface=", "\n", wpaSupStrFiltered)
        wpaSupConf["ctrl_interface"] = val.strip()
        val = Wifi._extractString("update_config=", "\n", wpaSupStrFiltered)
        wpaSupConf["update_config"] = int(val.strip())
        val = Wifi._extractString("country=", "\n", wpaSupStrFiltered)
        wpaSupConf["country"] = val.strip()
        wpaSupConf["networks"] = []
        for netPos in Wifi._findAll(wpaSupStrFiltered, "network="):
            rawNetwork = Wifi._extractString("network={", "}", wpaSupStrFiltered, netPos)
            network = dict()
            val = Wifi._extractString("ssid=", "\n", rawNetwork)
            network["ssid"] = val.strip("\"")
            val = Wifi._extractString("psk=", "\n", rawNetwork)
            network["psk"] = val.strip("\"")
            wpaSupConf["networks"].append(network)
        return wpaSupConf

    def wpaSupplicantConfToStr(wpaSupConf):
        """
        turns a wpa supplicant conf dict into a string which can be written to a file

        required dict keys:
        - ctrl_interface: str
        - update_config: int
        - country: str
        - networks: list
          - ssid: str
          - psk: str (must be a hashed psk)
        """
        wpaSupConfStr = "# autogenerated config by easyadsb sysmgmt\n"
        wpaSupConfStr += "ctrl_interface={}\n".format(wpaSupConf["ctrl_interface"])
        wpaSupConfStr += "update_config={}\n".format(wpaSupConf["update_config"])
        wpaSupConfStr += "country={}\n".format(wpaSupConf["country"])
        for network in wpaSupConf["networks"]:
            wpaSupConfStr += "network={\n"
            wpaSupConfStr += "\tssid=\"{}\"\n".format(network["ssid"])
            wpaSupConfStr += "\tpsk={}\n".format(network["psk"])
            wpaSupConfStr += "}\n"
        return wpaSupConfStr

    def _filterComments(raw, commentChar="#"):
        filtered = ""
        for line in raw.split("\n"):
            log.debug(line)
            if not line.startswith(commentChar):
                filtered += line + "\n"
            else:
                continue
        return filtered

    def _findAll(raw, sub):
        """
        yields all starting positions of sub in raw
        """
        start = 0
        while True:
            start = raw.find(sub, start)
            if start == -1:
                return
            yield start
            start += len(sub)

    def _extractString(skey, ekey, raw, offset=0):
        """
        returns the substring from raw between skey and ekey
        """
        start = raw.find(skey, offset)
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
