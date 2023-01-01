import QtQuick 2.15
import QtQuick.Layouts 1.15

import "../"


Item {
    signal push(string pageFile)

    ListView {
        anchors.fill: parent
        model: wifiSettingsModel
        delegate: Item {
            width: parent !== undefined ? parent.width : 0
            height: 80
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
                            Layout.preferredWidth: 70
                            text: signalLevel !== undefined ? signalLevel + "dBm" : "n/a"
                            font.pointSize: 6
                        }
                        Text {
                            Layout.preferredWidth: 70
                            text: frequency !== undefined ? frequency + "GHz" : "n/a"
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
        }
    }
}
