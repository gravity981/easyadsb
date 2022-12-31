

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

import "../"

View {
    id: root
    title: view.currentItem.title

    SwipeView {
        id: view
        anchors.top: parent.top
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
            onGoToSettings: {
                console.log("go to settings")
                root.push(Constants.kSettingsView)
            }
        }
    }

    /*Keyboard{
        id: keyboard
        anchors.top: header.bottom
        anchors.bottom: footer.top
        width: parent.width
        visible: false
    }*/

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