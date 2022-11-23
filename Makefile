.PHONY: all ublox dump1090mqtt monitor accesspoint

all: ublox dump1090mqtt monitor accesspoint

accesspoint:
	cd AccessPoint ;\
	docker build -t accesspoint .

ublox:
	docker build -t ghcr.io/gravity981/easyadsb/ublox -f Dockerfile.ublox .

dump1090mqtt:
	docker build -t ghcr.io/gravity981/easyadsb/dump1090mqtt -f Dockerfile.dump1090mqtt .

monitor:
	docker build -t ghcr.io/gravity981/easyadsb/monitor -f Dockerfile.monitor .

run-ublox: ublox
	docker run --rm --network=host --device=/dev/ttyAMA0 ghcr.io/gravity981/easyadsb/ublox

run-monitor: monitor
	docker run --rm --network=host ghcr.io/gravity981/easyadsb/monitor