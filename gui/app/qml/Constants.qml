pragma Singleton
import QtQuick 2.15

QtObject {
    readonly property string flagsPath: "../assets/flags-small/"
    function flagImageSourceFromCallsign(callsign) {
        let nation = null
        if (callsign == undefined) {
            nation = ""
        }
        else if (callsign.startsWith("N")) {
            nation = "N"
        }
        else if (callsign.startsWith("YV")) {
            nation = "YV"
        }
        else {
            nation = callsign.substring(0, callsign.indexOf('-'))
        }
        switch(nation) {
            case "HB":
                return flagsPath + "Switzerland.png"
            case "F":
                return flagsPath + "France.png"
            case "D":
                return flagsPath + "Germany.png"
            case "I":
                return flagsPath + "Italy.png"
            case "OE":
                return flagsPath + "Austria.png"
            case "EI":
                return flagsPath + "Ireland.png"
            case "9V":
                return flagsPath + "Singapore.png"
            case "EC":
                return flagsPath + "Spain.png"
            case "N":
                return flagsPath + "United_States_of_America.png"
            case "OH":
                return flagsPath + "Finland.png"
            case "SE":
                return flagsPath + "Sweden.png"
            case "SP":
                return flagsPath + "Poland.png"
            case "OK":
                return flagsPath + "Czech_Republic.png"
            case "CS":
                return flagsPath + "Portugal.png"
            case "HA":
                return flagsPath + "Hungary.png"
            case "YV":
                return flagsPath + "Venezuela.png"
            case "G":
                return flagsPath + "United_Kingdom.png"
            case "V8":
                return flagsPath + "Brunei.png"
            case "9H":
                return flagsPath + "Malta.png"
            case "OO":
                return flagsPath + "Belgium.png"
            case "PH":
                return flagsPath + "Netherlands.png"
            default:
                return ""
        }
    }

    function lastSeenColor(deltaSeconds) {
        let val = interpolate(deltaSeconds, 0, 1.0, 30, 0.0)
        if (val < 0) {
            val = 0
        }
        else if (val > 1) {
            val = 1
        }
        return Qt.hsva(0.3333, val, 0.75)
    }

    function interpolate(x, x0, y0, x1, y1) {
        // x0 and y0, start values
        // x1 and y1, end values
        // returns linear interpolated y for x
        return y0 + (x - x0)*(y1 - y0)/(x1 - x0)
    }
}