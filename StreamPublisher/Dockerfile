FROM arm32v7/python:3.11-alpine

# general
# =======
ENV SR_LOG_LEVEL INFO
# input mode can either be TCP or SERIAL
ENV SR_INPUT_MODE TCP

# serial
# ======
ENV SR_SERIAL_DEVICE /dev/ttyAMA0
ENV SR_SERIAL_BAUD 9600

# tcp
# ===
ENV SR_TCP_HOST localhost
ENV SR_TCP_PORT 30003

# MQTT
# ====
ENV SR_MQTT_HOST localhost
ENV SR_MQTT_PORT 1883
ENV SR_MQTT_CLIENT_NAME ""
ENV SR_MQTT_PUBLISH_TOPIC /streampublisher

WORKDIR /home
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY ./src ./app

CMD ["python", "/home/app/main.py"]
