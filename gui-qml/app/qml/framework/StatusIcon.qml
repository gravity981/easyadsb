import QtQuick 2.15

Image {
    property string activeSource
    property string inactiveSource
    property bool isActive: false

    fillMode: Image.PreserveAspectFit

    source: isActive ? activeSource : inactiveSource
}