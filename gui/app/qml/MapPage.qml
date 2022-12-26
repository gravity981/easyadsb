import QtQuick 2.15
import QtLocation 5.15
import QtPositioning 5.15
import QtQuick.Controls 2.15

Page {
    title: "Map"
    
    Plugin {
        id: mapPlugin
        name: "osm" // "mapboxgl", "esri", ...
        // specify plugin parameters if necessary
        // PluginParameter {
        //     name:
        //     value:
        // }
    }

    Map {
        id: map
        anchors.fill: parent
        plugin: mapPlugin
        copyrightsVisible: false
        zoomLevel: 8
        gesture.acceptedGestures: MapGestureArea.PinchGesture | MapGestureArea.PanGesture | MapGestureArea.FlickGesture

        MapCircle {
            center {
                latitude: positionModel.latitude ?? 0.0
                longitude: positionModel.longitude ?? 0.0
            }
            radius: 10000.0
            border.width: 3
            visible: positionModel.latitude !== undefined && positionModel.longitude !== undefined
        }

        MapCircle {
            center {
                latitude: positionModel.latitude ?? 0.0
                longitude: positionModel.longitude ?? 0.0
            }
            radius: 100000.0
            border.width: 3
            visible: positionModel.latitude !== undefined && positionModel.longitude !== undefined
        }

        MapQuickItem {
            coordinate {
                latitude: positionModel.latitude ?? 0.0
                longitude: positionModel.longitude ?? 0.0
            }
            sourceItem: Image {
                source: "../assets/icons/position_enabled.png"
                fillMode: Image.PreserveAspectFit
                visible: positionModel.latitude !== undefined && positionModel.longitude !== undefined    
                height: 100
                y: -height + 20
                x: -width/2
            }
        }

        MapItemView {
            model: trafficModel
            delegate: MapQuickItem {
                id: trafficEntry
                coordinate.latitude: latitude ?? 0.0
                coordinate.longitude: longitude ?? 0.0
                
                sourceItem: Column {
                        x: -planeIcon.width/2
                        y: -planeIcon.height/2
                    Image {
                        id: planeIcon
                        source: "../assets/icons/plane.png"
                        fillMode: Image.PreserveAspectFit
                        visible: latitude !== undefined && longitude !== undefined
                        height: 70
                        rotation: (track ?? 0) - 45
                    }
                    Text {
                        text: (callsign ?? "n/a")
                        font.pointSize: 8
                    }
                }
            }

            MapItemView {
                model: trafficModel
                delegate: MapPolyline {
                    id: trafficEntryTrack

                    // this property only exists to track position changes
                    readonly property double latlon: latitude + longitude

                    Component.onCompleted: trafficEntryTrack.addCoordinate(QtPositioning.coordinate(latitude, longitude))
                    onLatlonChanged: trafficEntryTrack.addCoordinate(QtPositioning.coordinate(latitude, longitude))

                    line.width: 3
                    line.color: 'green'
                }
            }
        }
    }

    Button {
        id: centerBtn
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        checkable: true
        background: Rectangle{
            anchors.fill: parent
            color: centerBtn.checked ? "blue" : "red"
        }
        width: 100
        height: 100
        opacity: 0.5
        onCheckedChanged: {
            if(checked) {
                map.center = Qt.binding(function() { return QtPositioning.coordinate(positionModel.latitude, positionModel.longitude)})
            }
            else {
                map.center = QtPositioning.coordinate(positionModel.latitude, positionModel.longitude)
            }
        }
    }
}