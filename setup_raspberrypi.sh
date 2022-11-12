#!/bin/bash

# UART configuartion
echo "Configure UART..."
isConfigured=$(cat /boot/config.txt | grep core_freq)
if [ -z "$isConfigured" ]; then
  cp /boot/config.txt /boot/config_backup.txt
  echo dtparam=spi=on >> /boot/config.txt
  echo dtoverlay=pi3-disable-bt >> /boot/config.txt
  echo core_freq=250 >> /boot/config.txt
  echo enable_uart=1 >> /boot/config.txt
  echo force_turbo=1 >> /boot/config.txt
  echo "configured /boot/config.txt"
  # TODO screen resolution is still wrong
else
  echo "/boot/config.txt already configured"
fi

isCmdLineConfigured=$(cat /boot/cmdline.txt | grep dwc_otg.lpm_enable)
if [ -z "$isCmdLineConfigured" ]; then
  cp /boot/cmdline.txt /boot/cmdline_backup.txt
  echo "dwc_otg.lpm_enable=0 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait quiet splash plymouth.ignore-serial-consoles" > /boot/cmdline.txt
  echo "configured /boot/cmdline.txt"
else
  echo "/boot/cmdline.txt already configured"
fi

echo "disable serial service"
systemctl stop serial-getty@ttyAMA0.service
systemctl disable serial-getty@ttyAMA0.service

echo "done"

# SDR configuration
echo "Configure SDR..."
blacklistFile=/etc/modprobe.d/blacklist-rtl2832.conf
if [ -f "$blacklistFile" ]; then
    echo "$blacklistFile already exists"
else
  echo "# Blacklist RTL2832 so docker container readsb can use the device" > $blacklistFile
  echo "blacklist rtl2832" >> $blacklistFile
  echo "blacklist dvb_usb_rtl28xxu" >> $blacklistFile
  echo "blacklist rtl2832_sdr" >> $blacklistFile
  echo "created $blacklistFile"
fi
echo "done"

# Install Docker
echo "Install Docker..."
dockerBin=$(which docker)
if [ -z "$dockerBin" ]; then
  curl -fsSL https://get.docker.com -o get-docker.sh
  source get-docker.sh
  usermod -aG docker $(whoami)
else
  dockerVersion=$(docker -v)
  echo "docker already installed: $dockerVersion"
fi
echo "done"

# Install easyadsb as a service
function installEasyADSBService() {
  systemctl link /home/pi/easyadsb/easyadsb.service
  systemctl enable easyadsb.service
}

echo "Install Easy ADS-B Service"
while true; do
    read -p "Do you wish to install Easy ADS-B as a service? " yn
    case $yn in
        [Yy]* ) installEasyADSBService; break;;
        [Nn]* ) break;;
        * ) echo "Please answer yes or no.";;
    esac
done
echo "done"

function replaceAutostart() {
  cp /etc/xdg/lxsession/LXDE-pi/autostart /etc/xdg/lxsession/LXDE-pi/autostart_backup
  # load chromium after boot and open the website in full screen mode
  echo "@xset s off" > /etc/xdg/lxsession/LXDE-pi/autostart
  echo "@xset -dpms" >> /etc/xdg/lxsession/LXDE-pi/autostart
  echo "@xset s noblank" >> /etc/xdg/lxsession/LXDE-pi/autostart
  echo "@chromium-browser --kiosk http://localhost:8080" >> /etc/xdg/lxsession/LXDE-pi/autostart
  # TODO add unclutter line for cursor
  # TODO page is not shown correctly
}

# Configure LXDE autostart
echo "Configure LXDE autostart"
isAutostartConfigured=$(cat /etc/xdg/lxsession/LXDE-pi/autostart | grep chromium-browser)
if [ -z "$isAutostartConfigured" ]; then
  while true; do
      read -p "Do you wish to Autostart Webbrowser with readsb? " yn
      case $yn in
          [Yy]* ) replaceAutostart; break;;
          [Nn]* ) break;;
          * ) echo "Please answer yes or no.";;
      esac
  done
else
  echo "/etc/xdg/lxsession/LXDE-pi/autostart already configured"
fi
echo "done"


# Reboot
while true; do
    read -p "Do you want to reboot now? " yn
    case $yn in
        [Yy]* ) reboot; break;;
        [Nn]* ) break;;
        * ) echo "Please answer yes or no.";;
    esac
done
