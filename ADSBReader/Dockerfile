FROM arm32v7/python:3.11-alpine

ENV GR_LOG_LEVEL INFO
ENV GR_SERIAL_DEVICE /dev/ttyAMA0
ENV GR_MQTT_HOST localhost
ENV GR_MQTT_PORT 1883
ENV GR_MQTT_CLIENT_NAME gps_reader

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src /app

CMD ["python", "/app/gps_reader.py"]
