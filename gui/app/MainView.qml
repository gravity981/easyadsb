

import QtQuick 2.15
import QtQuick.Controls 2.15

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
            text: "Easy ADS-B - " + view.currentItem.title
            color: "white"
            elide: Text.ElideRight
        }
    }
    
    SwipeView {
        id: view
        anchors.top: header.bottom
        anchors.bottom: footer.top
        width: parent.width
        z: -1

        SatellitesPage {}
        SatellitesPositionPage {}
        PositionPage {}
        TrafficPage {}
        SystemPage {}
    }

    PageIndicator {
        id: indicator

        count: view.count
        currentIndex: view.currentIndex

        anchors.bottom: view.bottom
        anchors.horizontalCenter: parent.horizontalCenter
    }

    Item {
        id: footer
        anchors.bottom: parent.bottom
        width: parent.width
        height: 100
        Rectangle {
            anchors.fill: parent
            color: "steelblue"
        }
        Button {
            id: "previousPageButton"
            anchors.left: parent.left
            width: height
            height: parent.height
            text: "<"
            onClicked: {
                var i = (view.currentIndex - 1)
                if (i < 0) {
                    i = view.count -1
                }
                view.setCurrentIndex(i)
            }
        }
        Button {
            id: "nextPageButton"
            anchors.right: parent.right
            width: height
            height: parent.height
            text: ">"
            onClicked: view.setCurrentIndex((view.currentIndex + 1) % view.count)
        }
        Button {
            id: testButton
            anchors.left: previousPageButton.right
            anchors.right: nextPageButton.left
            height: parent.height

            text: "info"
            onClicked: popup.open()
        }
    }

    Popup {
        id: popup
        anchors.centerIn: root
        width: 400
        height: 200
        parent: root
        // closePolicy: Popup.NoAutoClose
        
        Text {
            anchors.centerIn: parent
            text: "todo"
        }
        Button {
            anchors.bottom: parent.bottom
            text: "close"
            onClicked: popup.close()
        }
    }
}