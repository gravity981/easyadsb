FROM arm32v7/alpine:3.16.3 AS builder

LABEL org.opencontainers.image.source = "https://github.com/gravity981/easyadsb"

RUN apk add git make gcc musl-dev ncurses-dev librtlsdr-dev
WORKDIR /home
RUN git clone https://github.com/flightaware/dump1090.git && \
    cd dump1090 && \
    git reset --hard v7.2
RUN cd dump1090 && make RTLSDR=yes BLADERF=no HACKRF=no LIMESDR=no DUMP1090_VERSION=v7.2
 
FROM arm32v7/alpine:3.16.3 
WORKDIR /home
RUN apk add musl ncurses librtlsdr
COPY --from=builder /home/dump1090/dump1090 ./dump1090
CMD ["./dump1090", "--quiet", "--net-sbs-port", "30003"] 