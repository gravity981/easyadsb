import QtQuick 2.15
import QtQuick.Layouts 1.15

Page {
    title: "Traffic"
    Item {
        id: summary
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: 30
        Rectangle {
            anchors.fill: parent
        }
        Text {
            anchors.fill: parent
            text: "count: " + listview.count
            font.pointSize: 8
        }
    }
    ListView {
        id: listview
        anchors.top: summary.bottom
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        model: trafficModel
        z: -1
        delegate: Item {
            id: delegate
            width: listview.width
            height: 70
            Rectangle {
                anchors.fill: parent
                border.width: 1
                border.color: "#000000"
                color: mouseArea.pressed ? "#888888" : "#ffffff"
            }
            RowLayout {
                anchors.fill: parent
                spacing: 0
                Rectangle {
                    Layout.preferredWidth: 75
                    height: parent.height
                    border.width: 1
                    border.color: "#000000"
                    Image {
                        anchors.fill: parent
                        anchors.margins: 0
                        fillMode: Image.PreserveAspectFit
                        source: Constants.flagImageSourceFromCallsign(callsign)
                        Rectangle {
                            anchors.centerIn: parent
                            width: parent.paintedWidth
                            height: parent.paintedHeight
                            color: "#00000000"
                            border.width: 1
                            border.color: "#000000"
                        }
                    }
                }
                Rectangle {
                    Layout.preferredWidth: 135
                    height: parent.height
                    border.width: 1
                    border.color: "#000000"
                    Column {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: parent.left
                        anchors.leftMargin: 5
                        Text {
                            text: callsign ?? "n/a"
                            font.pointSize: 10
                        }
                        Text {
                            text: type ?? "n/a"
                            font.pointSize: 8
                        }
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    height: parent.height
                    border.width: 1
                    border.color: "#000000"
                    color: (latitude !== undefined && longitude !== undefined) ? "green": "#AAAAAA"
                    Text {
                        anchors.centerIn: parent
                        text: "p"
                        font.pointSize: 8
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    height: parent.height
                    border.width: 1
                    border.color: "#000000"
                    color: (altitude !== undefined) ? "green": "#AAAAAA"
                    Text {
                        anchors.centerIn: parent
                        text: "a"
                        font.pointSize: 8
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    height: parent.height
                    border.width: 1
                    border.color: "#000000"
                    color: (groundSpeed !== undefined) ? "green": "#AAAAAA"
                    Text {
                        anchors.centerIn: parent
                        text: "s"
                        font.pointSize: 8
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    height: parent.height
                    border.width: 1
                    border.color: "#000000"
                    color: (track !== undefined) ? "green": "#AAAAAA"
                    Text {
                        anchors.centerIn: parent
                        text: "t"
                        font.pointSize: 8
                    }
                }
                Rectangle {
                    Layout.preferredWidth: 120
                    height: parent.height
                    border.width: 1
                    border.color: "#000000"
                    Text {
                        anchors.centerIn: parent
                        text: lastSeen
                        font.pointSize: 8
                    }
                }
            }
            MouseArea {
                id: mouseArea
                anchors.fill: parent
                onClicked: detailsLoader.setSource("TrafficDetails.qml", model)
            }
        }
    }
    
    Loader {
        id: detailsLoader
        anchors.fill: parent
    }
}