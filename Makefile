image_base_path = ghcr.io/gravity981/easyadsb

.PHONY: all bme280 ublox dump1090 dump1090mqtt monitor

all: bme280 ublox dump1090 dump1090mqtt monitor

dump1090:
	docker build -t $(image_base_path)/dump1090 -f Dockerfile.dump1090 .

ublox:
	docker build -t $(image_base_path)/ublox -f Dockerfile.ublox .

dump1090mqtt:
	docker build -t $(image_base_path)/dump1090mqtt -f Dockerfile.dump1090mqtt .

monitor:
	docker build -t $(image_base_path)/monitor -f Dockerfile.monitor .

bme280:
	docker build -t $(image_base_path)/bme280 -f Dockerfile.bme280 .

run-ublox: ublox
	docker run --rm --network=host --device=/dev/ttyAMA0 $(image_base_path)/ublox

run-monitor: monitor
	docker run --rm --network=host $(image_base_path)/monitor

run-bme280: bme280
	docker run --rm --network=host --device=/dev/i2c-1 $(image_base_path)/bme280

run-dump1090: dump1090
	docker run --rm  --device=/dev/bus/usb --network=host -p 30003:30003 $(image_base_path)/dump1090

run-dump1090mqtt: dump1090mqtt
	docker run --rm --network=host $(image_base_path)/dump1090mqtt
