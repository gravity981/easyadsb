import QtQuick 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.15

import "../"


Page {
    id: root
    signal push(string pageFile)

    Flickable {
        anchors.fill: parent
        contentHeight: contentLayout.height
        ScrollBar.vertical: ScrollBar {}
        z: -1
        ColumnLayout {
            id: contentLayout
            width: parent.width
            MenuButton {
                Layout.fillWidth: true
                Layout.preferredHeight: 100
                text: "Wifi"
                onClicked: root.push("WifiPage.qml")
            }
            MenuButton {
                Layout.fillWidth: true
                Layout.preferredHeight: 100
                text: "Traffic"
                onClicked: root.push("TrafficSettingsPage.qml")
            }
            MenuButton {
                Layout.fillWidth: true
                Layout.preferredHeight: 100
                text: "Position"
                onClicked: root.push("PositionSettingsPage.qml")
            }
            MenuButton {
                Layout.fillWidth: true
                Layout.preferredHeight: 100
                text: "GDL90"
                onClicked: root.push("Gdl90SettingsPage.qml")
            }
        }
    }
}
