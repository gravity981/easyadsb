import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQml 2.15
import QtQuick.Window 2.15


ApplicationWindow {
    id: root
    visible: true
    contentOrientation: Qt.InvertedLandscapeOrientation // used for Popup

    Item {
        id: portrait
        width: 480
        height: 720

        AppScreen {
            anchors.fill: parent
            MainView {}
            SettingsView {}
        }

        transform: [
            Rotation { 
                origin.x: root.width / 2
                origin.y: root.height / 2
                angle: -90
            },
            Translate {
                y: -121
                x: -120
            }
        ]
    }
}