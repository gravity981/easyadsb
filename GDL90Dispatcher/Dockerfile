FROM arm32v7/ubuntu:bionic

# Install packages
RUN apt-get update && \
	apt-get install -y \
	vim \
	ifupdown \
	hostapd \
	isc-dhcp-server

# Configure Hostapd, use open config per default
ADD conf/hostapd_open.conf /etc/hostapd/hostapd.conf

# Configure DHCPD
ADD conf/dhcpd.conf /etc/dhcp/dhcpd.conf
RUN touch /var/lib/dhcp/dhcpd.leases

# Configure networking
ADD conf/interfaces /etc/network/interfaces

# Copy and execute init file
ADD conf/start.sh /start.sh
CMD ["/bin/sh", "/start.sh"]
