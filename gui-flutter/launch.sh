#!/bin/sh

startx &
sleep 5
export DISPLAY=:0
# rotation does not work properly, e.g. touch must also be rotated
#xrandr --output HDMI-1 --rotate left
sleep 2
#./build/linux/arm64/release/bundle/gui
xeyes