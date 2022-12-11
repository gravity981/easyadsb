import QtQuick 2.15

Page {
    title: "Sat Positions"
    Column {
        anchors.top: parent.top
        Text {
            text: "NavMode: " + positionModel.navMode
            font.pointSize: 8
        }
        Text {
            text: "count: " + satellitesModel.count
            font.pointSize: 8
        }
        Text {
            text: "used: " + satellitesModel.usedCount
            font.pointSize: 8
        }
    }
    Item {
        id: satMap
        anchors.centerIn: parent
        width: 400
        height: width

        Text {
            text: "N"
            anchors.bottom: parent.top
            anchors.horizontalCenter: parent.horizontalCenter
            verticalAlignment: Text.AlignBottom
        }
        Text {
            text: "W"
            anchors.left: parent.right
            anchors.verticalCenter: parent.verticalCenter
            horizontalAlignment: Text.AlignLeft
        }
        Text {
            text: "S"
            anchors.top: parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            verticalAlignment: Text.AlignTop
        }
        Text {
            text: "E"
            anchors.right: parent.left
            anchors.verticalCenter: parent.verticalCenter
            horizontalAlignment: Text.AlignRight
        }
        Rectangle {
            id: outerCircle
            anchors.centerIn: parent
            width: parent.width
            height: width
            border.color: "#0a2f4a"
            border.width: 1
            radius: width / 2
        }
        Rectangle {
            id: innerCircle
            anchors.centerIn: parent
            width: parent.width / 2
            height: width
            border.color: "#0a2f4a"
            border.width: 1
            radius: width / 2
        }
        Rectangle {
            id: centerPoint
            anchors.centerIn: parent
            width: 6
            height: width
            color: "#0a2f4a"
            radius: width / 2
        }
        Repeater {
            id: satellitePoints
            model: satellitesModel
            anchors.fill: parent
            Rectangle {
                property double evr: 1 - elv/90
                property double dx: (parent.width/2)*evr*Math.sin(toRadians(az))
                property double dy: -(parent.height/2)*evr*Math.cos(toRadians(az))

                function toRadians(angle) {
                    return angle * (Math.PI / 180)
                }

                x: parent.width/2 + dx - width/2
                y: parent.height/2 + dy - height/2
                visible: elv !== undefined && az != undefined
                width: 40
                height: width
                radius: width / 2
                color: isUsed ? "palegreen" : "paleturquoise"
                //onXChanged: console.log("svid: " + svid + ", evr: " + evr + ", dx: " + dx + ", x: " + x + ", sin(az): " + Math.sin(toRadians(az)))
                //onYChanged: console.log("svid: " + svid + ", evr: " + evr + ", dy: " + dy + ", y: " + y + ", cos(az): " + Math.cos(toRadians(az)))
                Text {
                    anchors.centerIn: parent
                    text: svid
                    font.pointSize: 6
                }
            }
        }
    }
}