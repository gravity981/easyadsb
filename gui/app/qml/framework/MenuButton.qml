import QtQuick 2.15
import QtQuick.Controls 2.15

import "../"


Button {
    id: root
    property bool isHighlighted

    contentItem: Text {
        id: content
        text: root.text
        verticalAlignment: Text.AlignVCenter
        horizontalAlignment: Text.AlignHCenter
        font.pointSize: 9
    }
    background: Rectangle {
        anchors.fill: parent
        color: parent.down ? Constants.darkGrey : (isHighlighted ? Constants.veryDarkGrey: Constants.lightGrey)
        border.color: parent.checked ? "firebrick" : Constants.borderBlack
        border.width: parent.checked ? 4 : 1
        radius: 4
    }
}
