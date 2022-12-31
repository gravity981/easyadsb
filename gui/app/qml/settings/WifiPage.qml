import QtQuick 2.15

Item {
    signal push(string pageFile)

    Rectangle {
        anchors.fill: parent
        color: "firebrick"
        Text {
            text: "under construction"
            anchors.centerIn: parent
        }
    }
}