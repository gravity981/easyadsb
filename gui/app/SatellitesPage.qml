import QtQuick 2.15

Page {
    title: "Satellites"
    Rectangle {
        anchors.top: parent.top
        height: title.height
        width: parent.width
        color: "white"
    }
    Text {
        id: title
        text: "NavMode: " + satellitesModel.testProperty
        anchors.top: parent.top
    }
    ListView {
        anchors.top: title.bottom
        anchors.bottom: parent.bottom
        width: parent.width
        model: satellitesModel
        z: -1
        delegate: Text {
            font.pointSize: 10
            text: "svid: " + svid + ", cno: " + cno + ", used: " + isUsed
        }
    }
}