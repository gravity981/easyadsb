#!/bin/sh

#export QT_DEBUG_PLUGINS=0
#export QT_QPA_EGLFS_DEBUG=1
#export QT_QPA_EGLFS_WIDTH=480
#export QT_QPA_EGLFS_HEIGHT=320
export QT_QPA_EGLFS_PHYSICAL_WIDTH=80
export QT_QPA_EGLFS_PHYSICAL_HEIGHT=55
export QT_QPA_EGLFS_HIDECURSOR=1
export QT_QPA_EGLFS_KMS_CONFIG=../kms.config
export QT_QPA_EGLFS_FORCEVSYNC=1
export GUI_LOG_LEVEL=INFO
export GUI_AIRCRAFT_IMAGES_PATH=/home/pi/aircraft_images
export GUI_MQTT_SATELLITE_TOPIC=/easyadsb/monitor/satellites
export GUI_MQTT_TRAFFIC_TOPIC=/easyadsb/monitor/traffic
export GUI_MQTT_POSITION_TOPIC=/easyadsb/monitor/position
export GUI_MQTT_STATUS_TOPIC=/easyadsb/monitor/status
export GUI_MQTT_SYSMGMT_INFO_TOPIC=/easyadsb/sysmgmt/info
export GUI_MQTT_SYSMGMT_CTRL_TOPIC=/easyadsb/sysmgmt/ctrl
cd app
/usr/bin/python gui.py -platform eglfs