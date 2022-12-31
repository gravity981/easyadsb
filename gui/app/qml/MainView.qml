

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
                isActive: positionModel.navMode !== undefined && positionModel.navMode != 1
            }
            StatusIcon {
                height: parent.height
                activeSource: "../assets/icons/wifi_enabled.png"
                inactiveSource: "../assets/icons/wifi_disabled.png"
                isActive: systemModel.wifi.ssid !== undefined
            }
        }
        MouseArea {
            anchors.fill: parent
            onClicked: keyboard.visible = !keyboard.visible
        }
    }
    
    SwipeView {
        id: view
        anchors.top: header.bottom
        anchors.bottom: footer.top
        width: parent.width
        interactive: false
        z: -1

        PositionPage {
            id: positionPage
        }
        TrafficPage {
            id: trafficPage
        }
        MapPage {
            id: mapPage
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

    Keyboard{
        id: keyboard
        anchors.top: header.bottom
        anchors.bottom: footer.top
        width: parent.width
        visible: false
    }

    RowLayout {
        id: footer
        anchors.bottom: parent.bottom
        width: parent.width
        height: 100
        spacing: 0
        MenuButton {
            Layout.fillWidth: true
            Layout.fillHeight: true
            text: "POS"
            isHighlighted: positionPage.SwipeView.isCurrentItem
            onClicked: view.setCurrentIndex(positionPage.SwipeView.index)

        }
        MenuButton {
            Layout.fillWidth: true
            Layout.fillHeight: true
            text: "TRF"
            isHighlighted: trafficPage.SwipeView.isCurrentItem
            onClicked: view.setCurrentIndex(trafficPage.SwipeView.index)

        }
        MenuButton {
            Layout.fillWidth: true
            Layout.fillHeight: true
            text: "MAP"
            isHighlighted: mapPage.SwipeView.isCurrentItem
            onClicked: view.setCurrentIndex(mapPage.SwipeView.index)

        }
        MenuButton {
            Layout.fillWidth: true
            Layout.fillHeight: true
            text: "SAT"
            isHighlighted: satellitesPage.SwipeView.isCurrentItem
            onClicked: view.setCurrentIndex(satellitesPage.SwipeView.index)

        }
        MenuButton {
            Layout.fillWidth: true
            Layout.fillHeight: true
            text: "STP"
            isHighlighted: satellitesPositionPage.SwipeView.isCurrentItem
            onClicked: view.setCurrentIndex(satellitesPositionPage.SwipeView.index)

        }
        MenuButton {
            Layout.fillWidth: true
            Layout.fillHeight: true
            text: "SYS"
            isHighlighted: systemPage.SwipeView.isCurrentItem
            onClicked: view.setCurrentIndex(systemPage.SwipeView.index)

        }
    }

    Rectangle {
        id: overlay
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
            color: Constants.transparent
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