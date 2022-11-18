FROM arm32v7/ubuntu:bionic

# Install packages
RUN apt-get update && \
	apt-get install -y \
	vim \
	ifupdown \
	hostapd \
	isc-dhcp-server

# Configure Hostapd, use open config per default
COPY ./conf/hostapd.conf /etc/hostapd/hostapd.conf

# Configure DHCPD
COPY ./conf/dhcpd.conf /etc/dhcp/dhcpd.conf
RUN touch /var/lib/dhcp/dhcpd.leases

# Configure networking
COPY ./conf/interfaces /etc/network/interfaces

# Copy and execute init file
COPY ./conf/start.sh /start.sh
CMD ["/bin/sh", "/start.sh"]
