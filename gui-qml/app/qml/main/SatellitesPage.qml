import QtQuick 2.15

import "../"


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
        text: "NavMode: " + positionModel.navMode + ", sat count: " + listview.count
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
            id: delegate
            width: listview.width
            height: 32
            Row {
                anchors.fill: parent
                
                Image {
                    id: countryFlag
                    height: parent.height
                    width: 50
                    fillMode: Image.PreserveAspectCrop
                    
                    states: [
                        State {
                            when: prn !== undefined && prn.toString().startsWith("R")
                            PropertyChanges {
                                target: countryFlag
                                source: Constants.getAssetPath("flags-small/Russian_Federation.png")
                            }
                        },
                        State {
                            when: prn !== undefined && prn.toString().startsWith("G")
                            PropertyChanges {
                                target: countryFlag
                                source: Constants.getAssetPath("flags-small/United_States_of_America.png")
                            }
                        }
                    ]

                    Rectangle {
                        anchors.fill:parent
                        border.width: 1
                        border.color: "#080808"
                        color: "#00000000"
                    }
                }
            
                Rectangle {
                    width: 60
                    height: parent.height
                    border.width: 1
                    border.color: "#080808"
                    Text {
                        anchors.fill: parent
                        anchors.leftMargin: 3
                        text: prn
                        font.pointSize: 8
                        verticalAlignment: Text.AlignVCenter
                    }
                }
                Rectangle {
                    width: delegate.width - x
                    height: parent.height
                    border.width: 1
                        border.color: "#080808"
                    Rectangle {
                        width: (cno ?? 0) / satellitesModel.maxCnoTotal * (parent.width)
                        height: parent.height
                        color: isUsed ? "palegreen" : "paleturquoise"
                        border.width: 1
                        border.color: "#080808"
                    }
                    Rectangle {
                        anchors.verticalCenter: parent.verticalCenter
                        width: 3
                        height: parent.height - 2*parent.border.width
                        visible: cno !== undefined
                        color: "#080808"
                        x: ((maxCno ?? 0) / satellitesModel.maxCnoTotal * (parent.width)) - width
                    }
                    Text {
                        anchors.left: parent.left
                        anchors.leftMargin: 10
                        height: parent.height
                        text: cno ?? "n/a"
                        font.pointSize: 8
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }
        }
    }
}