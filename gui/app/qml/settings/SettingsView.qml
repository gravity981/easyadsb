

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

import "../"


View {
    id: root
    title: "Settings"

    Rectangle {
        anchors.fill: parent
        color: "goldenrod"
    }

    StackView {
        id: view
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        z: -1
    }

    Button {
        anchors.centerIn: parent
        text: "pop"
        onClicked: root.popAll()
    }

    Keyboard{
        id: keyboard
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: parent.width
        visible: false
    }
}