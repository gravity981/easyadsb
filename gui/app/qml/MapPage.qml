import QtQuick 2.15
import QtLocation 5.15
import QtPositioning 5.15

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
        center: QtPositioning.coordinate(positionModel.latitude, positionModel.longitude)
        copyrightsVisible: false
        zoomLevel: 8

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
                y: -height
                x: -width/2
            }
        }
        MapItemView {
            model: trafficModel
            delegate: MapQuickItem {
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
                        text: callsign
                        font.pointSize: 8
                    }
                }
            }
        }
    }
    
}