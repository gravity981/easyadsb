.PHONY: all ublox dump1090mqtt monitor

all: ublox dump1090mqtt monitor

ublox:
	docker build -t ghcr.io/gravity981/easyadsb/ublox -f Dockerfile.ublox .

dump1090mqtt:
	docker build -t ghcr.io/gravity981/easyadsb/dump1090mqtt -f Dockerfile.dump1090mqtt .

monitor:
	docker build -t ghcr.io/gravity981/easyadsb/monitor -f Dockerfile.monitor .

run-ublox: ublox
	docker run --rm --network=host --device=/dev/ttyAMA0 ghcr.io/gravity981/easyadsb/ublox
