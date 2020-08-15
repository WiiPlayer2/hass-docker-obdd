FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV MQTT_BROKER=192.168.1.2
ENV MQTT_CLIENT_NAME=obd-service
ENV HASS_DISCOVERY_PREFIX=homeassistant
ENV OBD_WATCH_COMMANDS=ELM_VERSION,ELM_VOLTAGE,RPM
ENV NODE_ID=car
ENV IGNORE_OBD_CONNECTION=False
ENV CHECK_INTERVAL=30

CMD [ "python", "./main.py" ]
