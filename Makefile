image_base_path = ghcr.io/gravity981/easyadsb

.PHONY: all bme280 ublox dump1090 dump1090mqtt monitor accesspoint

all: ublox dump1090mqtt monitor accesspoint

dump1090:
	cd core ;\
	docker build -t $(image_base_path)/dump1090 -f Dockerfile.dump1090 .

accesspoint:
	cd core/AccessPoint ;\
	docker build -t accesspoint .

ublox:
	cd core ;\
	docker build -t $(image_base_path)/ublox -f Dockerfile.ublox .

dump1090mqtt:
	cd core ;\
	docker build -t $(image_base_path)/dump1090mqtt -f Dockerfile.dump1090mqtt .

monitor:
	cd core ;\
	docker build -t $(image_base_path)/monitor -f Dockerfile.monitor .

bme280:
	cd core ;\
	docker build -t $(image_base_path)/bme280 -f Dockerfile.bme280 .

run-ublox: ublox
	cd core ;\
	docker run --rm --network=host --device=/dev/ttyAMA0 $(image_base_path)/ublox

run-monitor: monitor
	cd core ;\
	docker run --rm --network=host $(image_base_path)/monitor

run-bme280: bme280
	cd core ;\
	docker run --rm --network=host --device=/dev/i2c-1 $(image_base_path)/bme280