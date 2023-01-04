import QtQuick 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.15

import "../"


Page {
    id: root
    property var keyboard
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
                text: "Set Callsign Filter"
                onClicked: keyboard.open("Set Callsign Filter", "", false)
            }
        }
    }

    Connections {
        target: keyboard
        function onConfirmed(cs) {
            if(!systemModel.setCallsignFilter(cs)) {
                console.log("set callsign filter " + cs + " failed")
            }
            keyboard.close()
        }
        function onCancel() {
            keyboard.close()
        }
    }
}
