FROM arm32v7/alpine:3.16.3

# Install packages
RUN apk add	ifupdown hostapd dhcp-server-vanilla

# Configure Hostapd
COPY ./conf/hostapd.conf /etc/hostapd/hostapd.conf

# Configure DHCPD
COPY ./conf/dhcpd.conf /etc/dhcp/dhcpd.conf
RUN touch /var/lib/dhcp/dhcpd.leases

# Configure networking
COPY ./conf/interfaces /etc/network/interfaces

# Copy and execute init file
COPY ./conf/start.sh /start.sh
CMD ["/bin/sh", "/start.sh"]
