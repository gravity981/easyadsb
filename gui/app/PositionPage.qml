import QtQuick 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.15

Page {
    id: root
    title: "Position"
    Flickable {
        anchors.fill: parent
        contentHeight: contentLayout.height

        ScrollBar.vertical: ScrollBar {}

        GridLayout {
            id: contentLayout
            width: root.width
            columns: 2
            rowSpacing: 0
            Text {
                text: "NavMode"
                font.pointSize: 8
            }
            Text {
                id: navModeText
                Layout.preferredWidth: 200
                text: "No Fix"
                font.pointSize: 8
                color: "red"
                states: [
                    State {
                        when: positionModel.navMode === 2
                        PropertyChanges {
                            target: navModeText
                            text: "2D"
                            color: "darkorange"
                        }
                    },
                    State {
                        when: positionModel.navMode === 3
                        PropertyChanges {
                            target: navModeText
                            text: "3D"
                            color: "darkgreen"
                        }
                    }
                ]
            }
            Text {
                text: "UTC Time"
                font.pointSize: 8
            }
            Text {
                text: positionModel.utcTime ?? "n/a"
                font.pointSize: 8
            }
            Text {
                text: "True Track"
                font.pointSize: 8
            }
            Text {
                text: positionModel.trueTrack !== undefined ? (positionModel.trueTrack + " °") : "n/a"
                font.pointSize: 8
            }
            Text {
                text: "Mag. Track"
                font.pointSize: 8
            }
            Text {
                text: positionModel.magneticTrack !== undefined ? (positionModel.magneticTrack + " °") : "n/a"
                font.pointSize: 8
            }
            Text {
                text: "Ground Speed"
                font.pointSize: 8
            }
            Text {
                text: positionModel.groundSpeedKnots !== undefined ? (positionModel.groundSpeedKnots + " kt") : "n/a"
                font.pointSize: 8
            }
            Text {
                text: "Ground Speed"
                font.pointSize: 8
            }
            Text {
                text: positionModel.groundSpeedKph !== undefined ? (positionModel.groundSpeedKph + " km/h") : "n/a"
                font.pointSize: 8
            }
            Text {
                text: "Latitude"
                font.pointSize: 8
            }
            Text {
                text: positionModel.latitude ?? "n/a"
                font.pointSize: 8
            }
            Text {
                text: "Longitude"
                font.pointSize: 8
            }
            Text {
                text: positionModel.longitude ?? "n/a"
                font.pointSize: 8
            }
            Text {
                text: "GPS AMSL Alt."
                font.pointSize: 8
            }
            Text {
                text: positionModel.altitudeMeter !== undefined ? (positionModel.altitudeMeter + " m") : "n/a"
                font.pointSize: 8
            }
            Text {
                text: "Pressure Alt."
                font.pointSize: 8
            }
            Text {
                text: positionModel.pressureAltitude !== undefined ? (positionModel.pressureAltitude + " m") : "n/a"
                font.pointSize: 8
            }
            Text {
                text: "Geoid Alt."
                font.pointSize: 8
            }
            Text {
                text: positionModel.geoAltitude !== undefined ? ((Math.round(positionModel.geoAltitude*100)/100) + " m") : "n/a"
                font.pointSize: 8
            }
            Text {
                text: "OAT"
                font.pointSize: 8
            }
            Text {
                text: positionModel.temperature !== undefined ? (positionModel.temperature + " °C") : "n/a"
                font.pointSize: 8
            }
            Text {
                text: "Humidity"
                font.pointSize: 8
            }
            Text {
                text: positionModel.humidity !== undefined ? (positionModel.humidity + " %H") : "n/a"
                font.pointSize: 8
            }
            Text {
                text: "Pressure"
                font.pointSize: 8
            }
            Text {
                text: positionModel.pressure !== undefined ? (positionModel.pressure + " hPa") : "n/a"
                font.pointSize: 8
            }
            Text {
                text: "pdop"
                font.pointSize: 8
            }
            Text {
                text: positionModel.pdop ?? "n/a"
                font.pointSize: 8
            }
            Text {
                text: "hdop"
                font.pointSize: 8
            }
            Text {
                text: positionModel.hdop ?? "n/a"
                font.pointSize: 8
            }
            Text {
                text: "vdop"
                font.pointSize: 8
            }
            Text {
                text: positionModel.vdop ?? "n/a"
                font.pointSize: 8
            }
            Text {
                text: "OpMode"
                font.pointSize: 8
            }
            Text {
                text: positionModel.opMode ?? "n/a"
                font.pointSize: 8
            }
        }
    }
}