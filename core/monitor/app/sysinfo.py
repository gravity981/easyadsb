import subprocess
import logging

logger = logging.getLogger("logger")


class Wifi:
    def getIwConfig(iface):
        process = subprocess.run(["iwconfig", iface], capture_output=True, encoding="utf-8")
        return process.stdout

    def parseIwConfig(iwconfigStr):
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
        iwconfig["quality"] = linkQuality

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
