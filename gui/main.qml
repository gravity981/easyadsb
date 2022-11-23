import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQml 2.15

ApplicationWindow {
    visible: true
    width: 600
    height: 500
    title: "HelloApp"

    Text {
        anchors.centerIn: parent
        text: "Hello World"
        font.pixelSize: 24
    }

    Timer {
        interval: 1000
        repeat: true
        onTriggered: console.log("ui is alive")
    }

}