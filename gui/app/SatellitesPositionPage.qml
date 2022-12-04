import QtQuick 2.15

Page {
    title: "Sat Positions"
    Rectangle {
        anchors.centerIn: parent
        width: parent.width
        height: width
        border.color: "#0a2f4a"
        border.width: 1
        radius: width / 2
    }

    Rectangle {
        anchors.centerIn: parent
        width: parent.width / 2
        height: width
        border.color: "#0a2f4a"
        border.width: 1
        radius: width / 2
    }

    Rectangle {
        anchors.centerIn: parent
        width: 2
        height: width
        color: "#0a2f4a"
        radius: width / 2
    }

    Repeater {
        model: satellitesModel
        anchors.fill: parent
        Rectangle {
            property double evr: 1 - elv/90
            property double dx: (parent.width/2)*evr*Math.sin(az)
            property double dy: (parent.height/2)*evr*Math.cos(az)
            x: parent.width/2 + dx
            y: parent.height/2 + dy
            visible: evr !== undefined && az != undefined
            width: 30
            height: width
            radius: width / 2
            color: isUsed ? "palegreen" : "paleturquoise"
            //onXChanged: console.log("evr: " + evr + ", dx: " + dx + ", x: " + x)
            //onYChanged: console.log("evr: " + evr + ", dy: " + dy + ", y: " + y)
            Text {
                anchors.centerIn: parent
                text: svid
                font.pointSize: 6
            }
        }
    }
}