import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    property var model

    Rectangle {
        anchors.fill: parent
    }
    Flickable {
        anchors.fill: parent
        contentHeight: contentLayout.height
        contentWidth: parent.width 
        ScrollBar.vertical: ScrollBar {}
        GridLayout {
            id: contentLayout
            width: parent.width
            columns: 2
            rowSpacing: 0
            Text {
                //Layout.preferredWidth: parent.width/2
                text: "Transponder ID"
                font.pointSize: 9
            }
            Text {
                //Layout.preferredWidth: parent.width/2
                text: model.id !== undefined ? model.id.toString(16) : "n/a"
                font.pointSize: 9
            }
            Text {
                text: "Callsign"
                font.pointSize: 9
            }
            Text {
                text: model.callsign ?? "n/a"
                font.pointSize: 9
            }
            Text {
                text: "Country"
                font.pointSize: 9
            }
            Image {
                Layout.preferredWidth: 150
                Layout.preferredHeight: paintedHeight
                fillMode: Image.PreserveAspectFit
                source: Constants.flagImageSourceFromCallsign(model.callsign)
                Rectangle {
                    anchors.centerIn: parent
                    width: parent.paintedWidth
                    height: parent.paintedHeight
                    color: "#00000000"
                    border.width: 1
                    border.color: "#000000"
                }
            }
            Text {
                text: "Type"
                font.pointSize: 9
            }
            Text {
                text: model.type ?? "n/a"
                font.pointSize: 9
            }
            Image {
                id: img
                Layout.columnSpan: 2
                Layout.preferredWidth: contentLayout.width - 20
                Layout.preferredHeight: paintedHeight
                Layout.alignment: Qt.AlignHCenter
                fillMode: Image.PreserveAspectFit
                source: model.imageSourcePath
                Rectangle {
                    anchors.centerIn: parent
                    width: parent.paintedWidth
                    height: parent.paintedHeight
                    color: "#00000000"
                    border.width: 1
                    border.color: "#000000"
                }
            }
            Text {
                text: "Category"
                font.pointSize: 9
            }
            Text {
                text: model.category ?? "n/a"
                font.pointSize: 9
            }
            Text {
                text: "Latitude"
                font.pointSize: 9
            }
            Text {
                text: model.latitude ?? "n/a"
                font.pointSize: 9
            }
            Text {
                text: "Longitude"
                font.pointSize: 9
            }
            Text {
                text: model.longitude ?? "n/a"
                font.pointSize: 9
            }
            Text {
                text: "Altitude"
                font.pointSize: 9
            }
            Text {
                text: model.altitude ?? "n/a"
                font.pointSize: 9
            }
            Text {
                text: "Track"
                font.pointSize: 9
            }
            Text {
                text: model.track ?? "n/a"
                font.pointSize: 9
            }
            Text {
                text: "Ground Speed"
                font.pointSize: 9
            }
            Text {
                text: model.groundSpeed ?? "n/a"
                font.pointSize: 9
            }
            Text {
                text: "Vertical Speed"
                font.pointSize: 9
            }
            Text {
                text: model.verticalSpeed ?? "n/a"
                font.pointSize: 9
            }
            Text {
                text: "Squawk"
                font.pointSize: 9
            }
            Text {
                text: model.squawk ?? "n/a"
                font.pointSize: 9
            }
            Text {
                text: "Alert"
                font.pointSize: 9
            }
            Text {
                text: model.alert ?? "n/a"
                font.pointSize: 9
            }
            Text {
                text: "Emergency"
                font.pointSize: 9
            }
            Text {
                text: model.emergency ?? "n/a"
                font.pointSize: 9
            }
            Text {
                text: "SPI (ident)"
                font.pointSize: 9
            }
            Text {
                text: model.spi ?? "n/a"
                font.pointSize: 9
            }
            Text {
                text: "Is on Ground"
                font.pointSize: 9
            }
            Text {
                text: model.isOnGround ?? "n/a"
                font.pointSize: 9
            }
            Text {
                text: "Last Seen UTC"
                font.pointSize: 9
            }
            Text {
                text: model.lastSeen ?? "n/a"
                font.pointSize: 9
            }
            Text {
                text: "Message Count"
                font.pointSize: 9
            }
            Text {
                text: model.msgCount ?? "n/a"
                font.pointSize: 9
            }
        }
    }

    Button {
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        height: 100
        onClicked: root.visible = false
        text: "close"
    }
}