import subprocess
import logging

logger = logging.getLogger("logger")


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
        logger.debug(iwconfigStr)
        iwconfig = dict()

        skey = "ESSID:"
        ekey = " "
        ssid = Wifi._extractString(skey, ekey, iwconfigStr)
        if ssid and '"' in ssid:
            ssid = ssid.strip('"')
        else:
            ssid = ""
        iwconfig["ssid"] = ssid

        skey = "Frequency:"
        ekey = " GHz"
        frequency = Wifi._extractString(skey, ekey, iwconfigStr)
        if frequency:
            try:
                frequency = float(frequency)
            except ValueError:
                frequency = ""
        else:
            frequency = ""
        iwconfig["frequency"] = frequency

        skey = "Access Point:"
        ekey = "  "
        ap = Wifi._extractString(skey, ekey, iwconfigStr)
        if ap:
            ap = ap.strip()
        else:
            ap = ""
        iwconfig["accesspoint"] = ap

        skey = "Link Quality="
        ekey = " "
        linkQuality = Wifi._extractString(skey, ekey, iwconfigStr)
        if linkQuality:
            linkQuality = linkQuality.split("/")
            if len(linkQuality) == 2:
                try:
                    linkQuality = round(float(linkQuality[0]) / float(linkQuality[1]), 3)
                except ValueError:
                    linkQuality = ""
            else:
                linkQuality = ""
        else:
            linkQuality = ""
        iwconfig["linkQuality"] = linkQuality

        skey = "Signal level="
        ekey = " dBm"
        signalLevel = Wifi._extractString(skey, ekey, iwconfigStr)
        if signalLevel:
            try:
                signalLevel = float(signalLevel)
            except ValueError:
                signalLevel = ""
        else:
            signalLevel = ""
        iwconfig["signalLevel"] = signalLevel

        return iwconfig

    def _extractString(skey, ekey, raw):
        start = raw.find(skey)
        if start < 0:
            return
        start += len(skey)
        end = raw.find(ekey, start)
        if end < 0:
            return
        return raw[start:end]


class Resources:
    """
    - memory usage --> cat /proc/meminfo

    """

    def getCpuTempFromSysfs():
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return f.read()

    def parseCpuTemperature(milliCelsius: str) -> float:
        """
        Returns CPU temperature in °C from milliCelsius string
        """
        logger.debug(milliCelsius)
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
        logger.debug(meminfo)
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
        logger.debug(stat)
        # todo parse stat string, (requires calculation over time)
        return 0.0

    def _getMemInfoValue(raw) -> float:
        # e.g. "MemTotal:        1917292 kB" returns 1917292
        try:
            return int(raw.split(":")[-1].strip().split()[0])
        except (ValueError, IndexError):
            return None
