import QtQuick 2.15
import QtQuick.Controls 2.15

import "../"

Item {
    id: root
    default property list<View> views

    Component.onCompleted: stackView.push(views[0])

    Item {
        id: header
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: 60
        Rectangle {
            anchors.fill: parent
            color: "steelblue"
        }
        Text {
            id: title
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            text: stackView.currentItem.title
            elide: Text.ElideRight
        }
        Row {
            anchors.right: parent.right
            height: parent.height
            StatusIcon {
                height: parent.height
                activeSource: Constants.getAssetPath("icons/updates_available.png")
                inactiveSource: ""
                isActive: true
                visible: false // bind to model
            }
            StatusIcon {
                height: parent.height
                activeSource: Constants.getAssetPath("icons/position_enabled.png")
                inactiveSource: Constants.getAssetPath("icons/position_disabled.png")
                isActive: positionModel.navMode !== undefined && positionModel.navMode != 1
            }
            StatusIcon {
                height: parent.height
                activeSource: Constants.getAssetPath("icons/wifi_enabled.png")
                inactiveSource: Constants.getAssetPath("icons/wifi_disabled.png")
                isActive: systemModel.wifi.ssid !== undefined
            }
        }
    }
    StackView {
        id: stackView
        anchors.top: header.bottom
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        z: -1

        pushEnter: Transition {
            YAnimator {
                from: (stackView.mirrored ? -1 : 1) * -stackView.height
                to: 0
                duration: 400
                easing.type: Easing.OutCubic
            }
        }

        pushExit: Transition {
            YAnimator {
                from: 0
                to: (stackView.mirrored ? -1 : 1) * stackView.height
                duration: 400
                easing.type: Easing.OutCubic
            }
        }

        popEnter: Transition {
            YAnimator {
                from: (stackView.mirrored ? -1 : 1) * stackView.height
                to: 0
                duration: 400
                easing.type: Easing.OutCubic
            }
        }

        popExit: Transition {
            YAnimator {
                from: 0
                to: (stackView.mirrored ? -1 : 1) * -stackView.height
                duration: 400
                easing.type: Easing.OutCubic
            }
        }
    }

    Connections {
        target: stackView.currentItem
        function onPop() {
            stackView.pop()
        }
        function onPopAll() {
            stackView.pop(null)
        }
        function onPush(index) {
            stackView.push(root.views[index])
        }
    }
}