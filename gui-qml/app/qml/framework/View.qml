import QtQuick 2.15

Item {
    default property alias content: content.data
    property string title
    
    signal pop
    signal popAll
    signal push(int id)

    Item {
        id: content
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
    }
}