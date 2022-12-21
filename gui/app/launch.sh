#!/bin/sh

#startx
#DISPLAY=:0.0 xrandr --output HDMI-1 --rotate left
#export QT_DEBUG_PLUGINS=0
#export QT_QPA_EGLFS_DEBUG=1
#export QT_QPA_EGLFS_WIDTH=480
#export QT_QPA_EGLFS_HEIGHT=320
export QT_QPA_EGLFS_PHYSICAL_WIDTH=80
export QT_QPA_EGLFS_PHYSICAL_HEIGHT=55
export QT_QPA_EGLFS_HIDECURSOR=1
export QT_QPA_EGLFS_KMS_CONFIG=kms.config
export QT_QPA_EGLFS_FORCEVSYNC=1
export GUI_LOG_LEVEL=INFO
/usr/bin/python main.py -platform eglfs