

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

import "../"


View {
    id: root
    title: "Settings"

    StackView {
        id: view
        anchors.top: parent.top
        anchors.bottom: footer.top
        anchors.left: parent.left
        anchors.right: parent.right
        z: -1
        initialItem: "MainPage.qml"
    }

    Connections {
        target: view.currentItem
        function onPush(pageFile) {
            view.push(Qt.createComponent(pageFile), {"keyboard": keyboard, "popup": popup})
        }
    }

    RowLayout {
        id: footer
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        height: 100
        MenuButton {
            Layout.fillWidth: true
            Layout.fillHeight: true
            text: "Close"
            onClicked: {
                if(view.depth > 1) {
                    view.pop(null)
                }
                else {
                    root.popAll()
                }
            }
        }
    }

    Keyboard{
        id: keyboard
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: parent.width
        visible: false
    }

    AppPopup {
        id: popup
        popup.width: 400
        popup.height: 400
    }
}