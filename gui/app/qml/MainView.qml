

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    anchors.fill: parent

    Item {
        id: header
        anchors.top: parent.top
        width: parent.width
        height: 60
        Rectangle {
            anchors.fill: parent
            color: "steelblue"
        }
        Text {
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            text: view.currentItem.title
            color: "white"
            elide: Text.ElideRight
        }

        Row {
            anchors.right: parent.right
            height: parent.height
            StatusIcon {
                height: parent.height
                activeSource: "../assets/icons/updates_available.png"
                inactiveSource: ""
                isActive: true
                visible: false // bind to model
            }
            StatusIcon {
                height: parent.height
                activeSource: "../assets/icons/position_enabled.png"
                inactiveSource: "../assets/icons/position_disabled.png"
                isActive: positionModel.navMode != 1
            }
            StatusIcon {
                height: parent.height
                activeSource: "../assets/icons/wifi_enabled.png"
                inactiveSource: "../assets/icons/wifi_disabled.png"
                isActive: systemModel.wifi.ssid != ""
            }
        }
    }
    
    SwipeView {
        id: view
        anchors.top: header.bottom
        anchors.bottom: footer.top
        width: parent.width
        z: -1

        PositionPage {
            id: positionPage
        }
        TrafficPage {
            id: trafficPage
        }
        SatellitesPage {
            id: satellitesPage
        }
        SatellitesPositionPage {
            id: satellitesPositionPage
        }
        SystemPage {
            id: systemPage
        }
    }

    RowLayout {
        id: footer
        anchors.bottom: parent.bottom
        width: parent.width
        height: 100
        spacing: 0
        Button {
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentItem: Text {
                text: "POS"
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pointSize: 9
            }
            background: Rectangle {
                anchors.fill: parent
                color: parent.down ? "#a6a6a6" : (positionPage.SwipeView.isCurrentItem ? "#888888": "#f6f6f6")
                border.color: "#26282a"
                border.width: 1
                radius: 4
            }
            onClicked: view.setCurrentIndex(positionPage.SwipeView.index)
        }
        Button {
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentItem: Text {
                text: "TRF"
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pointSize: 9
            }
            background: Rectangle {
                anchors.fill: parent
                color: parent.down ? "#a6a6a6" : (trafficPage.SwipeView.isCurrentItem ? "#888888": "#f6f6f6")
                border.color: "#26282a"
                border.width: 1
                radius: 4
            }
            onClicked: view.setCurrentIndex(trafficPage.SwipeView.index)
        }
        Button {
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentItem: Text {
                text: "SAT"
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pointSize: 9
            }
            background: Rectangle {
                anchors.fill: parent
                color: parent.down ? "#a6a6a6" : (satellitesPage.SwipeView.isCurrentItem ? "#888888": "#f6f6f6")
                border.color: "#26282a"
                border.width: 1
                radius: 4
            }
            onClicked: view.setCurrentIndex(satellitesPage.SwipeView.index)
        }
        Button {
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentItem: Text {
                text: "STP"
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pointSize: 9
            }
            background: Rectangle {
                anchors.fill: parent
                color: parent.down ? "#a6a6a6" : (satellitesPositionPage.SwipeView.isCurrentItem ? "#888888": "#f6f6f6")
                border.color: "#26282a"
                border.width: 1
                radius: 4
            }
            onClicked: view.setCurrentIndex(satellitesPositionPage.SwipeView.index)
        }
        Button {
            Layout.fillWidth: true
            Layout.fillHeight: true
            height: parent.height
            contentItem: Text {
                text: "SYS"
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font.pointSize: 9
            }
            background: Rectangle {
                anchors.fill: parent
                color: parent.down ? "#a6a6a6" : (systemPage.SwipeView.isCurrentItem ? "#888888": "#f6f6f6")
                border.color: "#26282a"
                border.width: 1
                radius: 4
            }
            onClicked: view.setCurrentIndex(systemPage.SwipeView.index)
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "#a0a0a0"
        opacity: 0.5
        visible: popup.visible
    }

    Popup {
        id: popup
        anchors.centerIn: root
        width: 400
        height: 200
        parent: root
        closePolicy: Popup.NoAutoClose
        modal: true
        visible: !systemModel.isAlive
        Overlay.modal: Rectangle {
            //make overlay transparent because it is not shown correctly because of transformation (main.qml)
            color: "#00000000"
        }
        Text {
            anchors.fill: parent
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            text: "Waiting for System..."
            wrapMode: Text.WordWrap
        }

    }
}