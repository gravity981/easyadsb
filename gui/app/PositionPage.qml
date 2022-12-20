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
            }
            Text {
                id: navModeText
                text: "No Fix"
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
                text: "OpMode"
            }
            Text {
                text: positionModel.opMode
            }
            Text {
                text: "pdop"
            }
            Text {
                text: positionModel.pdop ?? "n/a"
            }
            Text {
                text: "hdop"
            }
            Text {
                text: positionModel.hdop ?? "n/a"
            }
            Text {
                text: "vdop"
            }
            Text {
                text: positionModel.vdop ?? "n/a"
            }
            Text {
                text: "True Track"
            }
            Text {
                text: positionModel.trueTrack ?? "n/a"
            }
            Text {
                text: "Mag. Track"
            }
            Text {
                text: positionModel.magneticTrack ?? "n/a"
            }
            Text {
                text: "GS kt"
            }
            Text {
                text: positionModel.groundSpeedKnots ?? "n/a"
            }
            Text {
                text: "GS km/h"
            }
            Text {
                text: positionModel.groundSpeedKph ?? "n/a"
            }
            Text {
                text: "Latitude"
            }
            Text {
                text: positionModel.latitude ?? "n/a"
            }
            Text {
                text: "Longitude"
            }
            Text {
                text: positionModel.longitude ?? "n/a"
            }
            Text {
                text: "Alt. m"
            }
            Text {
                text: positionModel.altitudeMeter ?? "n/a"
            }
            Text {
                text: "Sep. m"
            }
            Text {
                text: positionModel.separationMeter ?? "n/a"
            }
            Text {
                text: "UTC Time"
            }
            Text {
                text: positionModel.utcTime
            }
            Text {
                text: "Temp. °C"
            }
            Text {
                text: positionModel.temperature ?? "n/a"
            }
            Text {
                text: "Humidity %H"
            }
            Text {
                text: positionModel.humidity ?? "n/a"
            }
            Text {
                text: "Pressure hPa"
            }
            Text {
                text: positionModel.pressure ?? "n/a"
            }
            Text {
                text: "Pressure Alt. m"
            }
            Text {
                text: positionModel.pressureAltitude ?? "n/a"
            }
        }
    }
}