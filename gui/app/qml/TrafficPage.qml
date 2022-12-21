import QtQuick 2.15

Page {
    title: "Traffic"
    ListView {
        id: listview
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: parent.width
        model: trafficModel
        z: -1
        delegate: Item {
            width: listview.width
            height: 45
            Text {
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                font.pointSize: 8
                text: id + " " + callsign + " " + model
            }
        }
    }
}