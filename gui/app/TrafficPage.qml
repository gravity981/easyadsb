import QtQuick 2.15

Page {
    title: "Traffic"
    Text {
        anchors.fill: parent
        wrapMode: Text.WrapAnywhere
        text: JSON.stringify(trafficModel)
    }
}