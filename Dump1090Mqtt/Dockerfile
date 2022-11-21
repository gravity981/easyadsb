FROM arm32v7/python:3.11-alpine

LABEL org.opencontainers.image.source = "https://github.com/gravity981/easyadsb"

# general
# =======
ENV DU_LOG_LEVEL INFO

# tcp
# ===
ENV DU_TCP_HOST localhost
ENV DU_TCP_PORT 30003

# MQTT
# ====
ENV DU_MQTT_HOST localhost
ENV DU_MQTT_PORT 1883
ENV DU_MQTT_CLIENT_NAME ""
ENV DU_MQTT_PUBLISH_TOPIC /easyadsb/dump1090/sbs

WORKDIR /home
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app ./app

CMD ["python", "/home/app/main.py"]
