import QtQuick 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.15

Page {
    title: "System"
    Flickable {
        anchors.fill: parent
        contentHeight: contentLayout.height

        ScrollBar.vertical: ScrollBar {}

        GridLayout {
            id: contentLayout
            width: root.width
            columns: 2
            rowSpacing: 0
            
            Text {
                Layout.columnSpan: 2
                text: "Wifi"
            }
            Text {
                text: "SSID"
                font.pointSize: 8
            }
            Text {
                text: systemModel.wifi.ssid ?? "n/a"
                font.pointSize: 8
            }
            Text {
                text: "Frequency"
                font.pointSize: 8
            }
            Text {
                text: systemModel.wifi.frequency !== undefined ? (systemModel.wifi.frequency + " GHz") : "n/a"
                font.pointSize: 8
            }
            Text {
                text: "Access Point"
                font.pointSize: 8
            }
            Text {
                text: systemModel.wifi.accesspoint ?? "n/a"
                font.pointSize: 8
            }
            Text {
                text: "Link Quality"
                font.pointSize: 8
            }
            Text {
                text: systemModel.wifi.linkQuality !== undefined ? ((Math.round(systemModel.wifi.linkQuality * 10000)/100) + " %") : "n/a"
                font.pointSize: 8
            }
            Text {
                text: "Signal Level"
                font.pointSize: 8
            }
            Text {
                text: systemModel.wifi.signalLevel !== undefined ? (systemModel.wifi.signalLevel + " dBm") : "n/a"
                font.pointSize: 8
            }
            Button {
                Layout.columnSpan: 2
                text: "add wifi"
                onClicked: systemModel.addWifi("dummyWifi","secretPassword123")
            }

            Text {
                Layout.columnSpan: 2
                text: "GDL90"
            }
            Text {
                text: "Active"
                font.pointSize: 8
            }
            Text {
                text: systemModel.gdl90.isActive ?? "n/a"
                font.pointSize: 8
            }
            Text {
                text: "IP"
                font.pointSize: 8
            }
            Text {
                text: systemModel.gdl90.ip ?? "n/a"
                font.pointSize: 8
            }
            Text {
                text: "Net Mask"
                font.pointSize: 8
            }
            Text {
                text: systemModel.gdl90.netMask ?? "n/a"
                font.pointSize: 8
            }
            Text {
                text: "Broadcast IP"
                font.pointSize: 8
            }
            Text {
                text: systemModel.gdl90.broadcastIp ?? "n/a"
                font.pointSize: 8
            }
            Text {
                text: "NIC"
                font.pointSize: 8
            }
            Text {
                text: systemModel.gdl90.nic ?? "n/a"
                font.pointSize: 8
            }
            Text {
                text: "Port"
                font.pointSize: 8
            }
            Text {
                text: systemModel.gdl90.port ?? "n/a"
                font.pointSize: 8
            }

            Text {
                Layout.columnSpan: 2
                text: "Resources"
                
            }
            Text {
                text: "Total Mem"
                font.pointSize: 8
            }
            Text {
                text: systemModel.resources.memTotal !== undefined ? (systemModel.resources.memTotal + " kB") : "n/a"
                font.pointSize: 8
            }
            Text {
                text: "Free Mem"
                font.pointSize: 8
            }
            Text {
                text: systemModel.resources.memFree !== undefined ? (systemModel.resources.memFree + " kB") : "n/a"
                font.pointSize: 8
            }
            Text {
                text: "Swap Cached"
                font.pointSize: 8
            }
            Text {
                text: systemModel.resources.swapCached !== undefined ? (systemModel.resources.swapCached + " kB") : "n/a"
                font.pointSize: 8
            }
            Text {
                text: "CPU Temp."
                font.pointSize: 8
            }
            Text {
                text: systemModel.resources.cpuTemp !== undefined ? (systemModel.resources.cpuTemp + " °C") : "n/a"
                font.pointSize: 8
            }
            Text {
                text: "CPU Usage"
                font.pointSize: 8
            }
            Text {
                text: systemModel.resources.cpuUsage !== undefined ? (systemModel.resources.cpuUsage + " %") : "n/a"
                font.pointSize: 8
            }
        }
    }
}