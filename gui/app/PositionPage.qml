import QtQuick 2.15

Page {
    title: "Position"

    Text {
        anchors.fill: parent
        text: JSON.stringify(positionModel)
        wrapMode: Text.WrapAnywhere
    }
}