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
        anchors.top: parent.top
        text: "NavMode: " + satellitesModel.testProperty + ", sat count: " + listview.count
        font.pointSize: 8
    }
    ListView {
        id: listview
        anchors.top: title.bottom
        anchors.bottom: parent.bottom
        width: parent.width
        model: satellitesModel
        z: -1
        delegate: Item {
            width: listview.width
            height: 45
            Rectangle {
                width: (cno ?? 0) / 80.0 * parent.width 
                height: parent.height
                color: isUsed ? "palegreen" : "paleturquoise"
            }
            Text{
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                font.pointSize: 10
                text: "svid: " + svid + ", cno: " + (cno ?? 0)
            }
        }
    }
}