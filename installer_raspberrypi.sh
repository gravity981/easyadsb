#!/bin/bash

# UART configuartion
echo "Configure UART..."
isConfigured=$(cat /boot/config.txt | grep core_freq)
if [ -z "$isConfigured" ]; then
  cp /boot/config.txt /boot/config_backup.txt
  echo dtparam=spi=on >> /boot/config.txt
  echo dtoverlay=disable-bt >> /boot/config.txt
  echo core_freq=250 >> /boot/config.txt
  echo enable_uart=1 >> /boot/config.txt
  echo force_turbo=1 >> /boot/config.txt
  echo "configured /boot/config.txt"
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

echo "disable serial-getty service"
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
  source get-docker.sh # FIXME: scripts exits after this
  usermod -aG docker $(whoami)
  rm get-docker.sh
else
  dockerVersion=$(docker -v)
  echo "docker already installed: $dockerVersion"
fi
echo "done"

# FIXME Install easyadsb as a service, service files changed
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

# TODO remove this
# Configure LXDE autostart
function replaceAutostart() {
  cp /etc/xdg/lxsession/LXDE-pi/autostart /etc/xdg/lxsession/LXDE-pi/autostart_backup
  # load chromium after boot and open the website in full screen mode
  echo "@xset s off" > /etc/xdg/lxsession/LXDE-pi/autostart
  echo "@xset -dpms" >> /etc/xdg/lxsession/LXDE-pi/autostart
  echo "@xset s noblank" >> /etc/xdg/lxsession/LXDE-pi/autostart
  echo "@chromium-browser --kiosk http://localhost:8080" >> /etc/xdg/lxsession/LXDE-pi/autostart
}

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

# FIXME THIS DOES NOT WORK
# Switch resolution to 720x480 (3.5" HDMI LCD Display)

function writeXprofile() {
  # FIXME: the xrandr command seems to be correct but it does not get executed automatically
  echo "#!/bin/bash" > /home/pi/.xprofile
  echo "xrandr -display :0.0 -s 720x480" >> /home/pi/.xprofile
  chmod +x /home/pi/.xprofile
  chown pi:pi /home/pi/.xprofile
}
while true; do
      read -p "Do you wish to change the screen resolution to 720x480? " yn
      case $yn in
          [Yy]* ) writeXprofile; break;;
          [Nn]* ) break;;
          * ) echo "Please answer yes or no.";;
      esac
  done


# TODO install pyqt5 dependencies (QtQml)
# sudo apt install python3-pyqt5 python3-pyqt5.qtquick
# sudo apt install qml-module-qtlocation
# sudo apt install qml-module-qtpositioning
# TODO setup to boot into console. disable boot into desktop

# TODO setup init i2c and load kernel modules


# Reboot
while true; do
    read -p "Do you want to reboot now? " yn
    case $yn in
        [Yy]* ) reboot; break;;
        [Nn]* ) break;;
        * ) echo "Please answer yes or no.";;
    esac
done
