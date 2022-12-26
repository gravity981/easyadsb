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

        ScrollBar.vertical: ScrollBar {}
        GridLayout {
            id: contentLayout
            width: parent.width
            columns: 2
            rowSpacing: 0
            Text {
                text: "Transponder ID"
            }
            Text {
                text: model.id ?? "n/a"
            }
            Text {
                text: "Callsign"
            }
            Text {
                text: model.callsign ?? "n/a"
            }
            Text {
                text: "Type"
            }
            Text {
                text: model.type ?? "n/a"
            }
            Text {
                text: "Category"
            }
            Text {
                text: model.category ?? "n/a"
            }
            Text {
                text: "Latitude"
            }
            Text {
                text: model.latitude ?? "n/a"
            }
            Text {
                text: "Longitude"
            }
            Text {
                text: model.longitude ?? "n/a"
            }
            Text {
                text: "Altitude"
            }
            Text {
                text: model.altitude ?? "n/a"
            }
            Text {
                text: "Track"
            }
            Text {
                text: model.track ?? "n/a"
            }
            Text {
                text: "Ground Speed"
            }
            Text {
                text: model.groundSpeed ?? "n/a"
            }
            Text {
                text: "Vertical Speed"
            }
            Text {
                text: model.verticalSpeed ?? "n/a"
            }
            Text {
                text: "Squawk"
            }
            Text {
                text: model.squawk ?? "n/a"
            }
            Text {
                text: "Alert"
            }
            Text {
                text: model.alert ?? "n/a"
            }
            Text {
                text: "Emergency"
            }
            Text {
                text: model.emergency ?? "n/a"
            }
            Text {
                text: "SPI (ident)"
            }
            Text {
                text: model.spi ?? "n/a"
            }
            Text {
                text: "Is on Ground"
            }
            Text {
                text: model.isOnGround ?? "n/a"
            }
            Text {
                text: "Last Seen UTC"
            }
            Text {
                text: model.lastSeen ?? "n/a"
            }
            Text {
                text: "Message Count"
            }
            Text {
                text: model.msgCount ?? "n/aaaaaa"
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