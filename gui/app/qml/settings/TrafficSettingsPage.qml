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
                text: "Clear History"
                onClicked: trafficModel.clearHistory()
            }
            MenuButton {
                id: btn
                Layout.fillWidth: true
                Layout.preferredHeight: 100
                checkable: true
                text: "Enable Auto Cleanup"
                onClicked: {
                    if(!trafficModel.setAutoCleanup(btn.checked)) {
                        console.log("set auto cleanup not successful, put it to " + !btn.checked)
                        btn.checked = !btn.checked
                    }
                }
            }
        }
    }
}
