FROM arm32v7/python:3.11-alpine

# general
# =======
ENV MO_LOG_LEVEL INFO
ENV MO_MQTT_HOST localhost
ENV MO_MQTT_PORT 1883
ENV MO_MQTT_CLIENT_NAME ""
ENV MO_MQTT_NMEA_TOPIC /gps/nmea
ENV MO_MQTT_SBS_TOPIC /adsb/sbs
ENV MO_GDL90_BROADCAST_IP 192.168.77.255
ENV MO_GDL90_PORT 4000

WORKDIR /home
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY ./data ./app/data
COPY ./src ./app

CMD ["python", "/home/app/main.py"]
