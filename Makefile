.PHONY: all ublox dump1090mqtt monitor accesspoint

all: ublox dump1090mqtt monitor accesspoint

accesspoint:
	cd core/AccessPoint ;\
	docker build -t accesspoint .

ublox:
	cd core ;\
	docker build -t ghcr.io/gravity981/easyadsb/ublox -f Dockerfile.ublox .

dump1090mqtt:
	cd core ;\
	docker build -t ghcr.io/gravity981/easyadsb/dump1090mqtt -f Dockerfile.dump1090mqtt .

monitor:
	cd core ;\
	docker build -t ghcr.io/gravity981/easyadsb/monitor -f Dockerfile.monitor .

bme280:
	cd core ;\
	docker build -t ghcr.io/gravity981/easyadsb/bme280 -f Dockerfile.bme280 .

run-ublox: ublox
	cd core ;\
	docker run --rm --network=host --device=/dev/ttyAMA0 ghcr.io/gravity981/easyadsb/ublox

run-monitor: monitor
	cd core ;\
	docker run --rm --network=host ghcr.io/gravity981/easyadsb/monitor

run-bme280: bme280
	cd core ;\
	docker run --rm --network=host --device=/dev/i2c-1 ghcr.io/gravity981/easyadsb/bme280