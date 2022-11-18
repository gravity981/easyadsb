FROM arm32v7/python:3.11-alpine

# general
# =======
ENV GD_LOG_LEVEL DEBUG
ENV GD_MQTT_HOST localhost
ENV GD_MQTT_PORT 1883
ENV GD_MQTT_CLIENT_NAME ""
ENV GD_MQTT_NMEA_TOPIC /gps/nmea
ENV GD_MQTT_SBS_TOPIC /adsb/sbs
ENV GD_MQTT_PUBLISH_TOPIC /gdl90

WORKDIR /home
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY ./src ./app

CMD ["python", "/home/app/main.py"]
