import QtQuick 2.15
import QtQuick.Layouts 1.15

import "../"


Item {
    property var keyboard
    property var popup

    signal push(string pageFile)

    QtObject {
        id: internal
        property string editSsid
    }

    ListView {
        anchors.top: parent.top
        anchors.bottom: buttonsLayout.top
        anchors.left: parent.left
        anchors.right: parent.right
        model: wifiSettingsModel
        delegate: Item {
            width: parent !== null ? parent.width : 0
            height: 80
            Rectangle {
                anchors.fill: parent
                color: Constants.darkGrey
                visible: mouseArea.pressed
            }
            RowLayout {
                height: parent.height
                spacing: 0
                Item {
                    Layout.preferredWidth: 40
                    height: parent.height
                    Rectangle {
                        anchors.centerIn: parent
                        width: 30
                        height: width
                        radius: width / 2
                        color: isConnected ? "green" : Constants.transparent
                        border.width: isKnown ? 3 : 0
                        border.color: "green"
                    }
                }
                Column {
                    Layout.preferredWidth: 400
                    height: parent.height
                    RowLayout {
                        Text {
                            Layout.preferredWidth: 250
                            text: ssid
                            elide: Text.ElideRight
                            font.pointSize: 8
                        }
                        Item {
                            Layout.preferredWidth: 100
                            Rectangle {
                                anchors.centerIn: parent
                                width: 60
                                height: 20
                                color: Constants.transparent
                                border.width: 1
                                border.color: "#000000"
                                Rectangle {
                                    anchors.left: parent.left
                                    height: parent.height
                                    width: (linkQuality ?? 0) * parent.width
                                    color: "#000000"
                                }
                            }
                        }
                    }
                    RowLayout {
                        Text {
                            Layout.preferredWidth: 180
                            text: accesspoint ?? "n/a"
                            font.pointSize: 6
                        }
                        Text {
                            Layout.preferredWidth: 100
                            text: frequency !== undefined ? frequency + "GHz" : "n/a"
                            font.pointSize: 6
                        }
                        Text {
                            Layout.preferredWidth: 100
                            text: signalLevel !== undefined ? signalLevel + "dBm" : "n/a"
                            font.pointSize: 6
                        }
                    }
                }
                Text {
                    Layout.preferredWidth: 10
                    height: parent.height
                    text: "L"
                    font.pointSize: 8
                    visible: isEncrypted ?? false
                }
            }
            Rectangle {
                anchors.fill: parent
                color: Constants.transparent
                border.width: 1
                border.color: "#000000"
            }
            MouseArea {
                id: mouseArea
                anchors.fill: parent
                onClicked: {
                    if(internal.editSsid) {
                        console.log("a change is already in progress, cannot start changing " + ssid)
                    }
                    else {
                        internal.editSsid = ssid
                    }
                    if(!isKnown){
                        keyboard.open("Add Wifi, enter PSK for " + ssid, "")
                    }
                    else {
                        popup.show("Remove Wifi \"" + ssid + "\"?", true, true)
                    }
                }
            }
        }
    }
    RowLayout {
        id: buttonsLayout
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        height: 80
        MenuButton {
            Layout.fillWidth: true
            Layout.fillHeight: true
            text: "save"
            onClicked: wifiSettingsModel.saveChanges()
        }
        MenuButton {
            Layout.fillWidth: true
            Layout.fillHeight: true
            text: "Force Reconnect"
            onClicked: wifiSettingsModel.forceReconnect()
        }
    }

    Connections {
        target: keyboard
        function onConfirmed(psk) {
            wifiSettingsModel.addWifi(internal.editSsid, psk)
            internal.editSsid = ""
            keyboard.close()
        }
        function onCancel() {
            internal.editSsid = ""
            keyboard.close()
        }
    }

    Connections {
        target: popup
        function onConfirmed() {
            wifiSettingsModel.removeWifi(internal.editSsid)
            internal.editSsid = ""
            popup.hide()
        }
        function onCancel() {
            internal.editSsid = ""
            popup.hide()
        }
    }
}
