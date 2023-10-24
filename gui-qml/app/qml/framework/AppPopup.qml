import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

import "../"

Item {
    id: root
    
    property alias popup: popup
    property alias text: textContent.text
    property alias canConfirm: confirmButton.visible
    property alias canCancel: cancelButton.visible

    signal confirmed
    signal cancel

    function show(txt, canConfirm, canCancel) {
        textContent.text = txt
        confirmButton.visible = canConfirm
        cancelButton.visible = canCancel
        root.visible = true
    }

    function hide() {
        root.visible = false
    }

    anchors.fill: parent
    visible: false

    Rectangle {
        id: overlay
        anchors.fill: parent
        color: "#a0a0a0"
        opacity: 0.5
        MouseArea {
            id: clickBlocker
            anchors.fill: parent
        }
    }

    Popup {
        id: popup
        anchors.centerIn: root
        width: 400
        height: 200
        closePolicy: Popup.NoAutoClose
        modal: true
        visible: root.visible

        Overlay.modal: Rectangle {
            //make overlay transparent because it is not shown correctly because of transformation (main.qml)
            color: Constants.transparent
        }
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 5
            Text {
                id: textContent
                Layout.fillHeight: true
                Layout.fillWidth: true
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
            }
            RowLayout {
                //Layout.preferredHeight: 60
                Layout.fillWidth: true
                MenuButton {
                    id: cancelButton
                    Layout.fillWidth: true
                    Layout.preferredHeight: 80 //parent.height
                    text: "cancel"
                    onClicked: root.cancel()
                }
                MenuButton {
                    id: confirmButton
                    Layout.fillWidth: true
                    Layout.preferredHeight: 80 //parent.height
                    text: "confirm"
                    onClicked: root.confirmed()
                }
            }
        }
    }
}
