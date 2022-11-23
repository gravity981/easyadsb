import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQml 2.15

ApplicationWindow {
    visible: true
    width: 600
    height: 500
    title: "Easy ADS-B"

    Text {
        anchors.centerIn: parent
        text: "Easy ADS-B"
        font.pixelSize: 24
    }

    Button {
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        width: 300
        height: 200
        text: "touch test"
    }

}