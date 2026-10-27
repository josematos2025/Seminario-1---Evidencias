## ~/compose.yaml
```
services:
  mosquitto:
    image: eclipse-mosquitto:2
    restart: unless-stopped
    volumes:
      - ./mosquitto/config/mosquitto.conf:/mosquitto/config/mosquitto.conf:ro
    networks:
      - iot_net

  iot:
    build:
      context: ./iot
    restart: unless-stopped
    environment:
      MQTT_HOST: mosquitto
      MQTT_PORT: "1883"
    depends_on:
      - mosquitto
    networks:
      - iot_net

  captura:
    image: nicolaka/netshoot:latest
    restart: unless-stopped
    network_mode: "service:mosquitto"
    depends_on:
      - mosquitto
    cap_add:
      - NET_RAW
      - NET_ADMIN
    volumes:
      - ./capturas:/capturas
    command:
      - tcpdump
      - -i
      - eth0
      - -nn
      - -s
      - "0"
      - -U
      - -w
      - /capturas/iot-mqtt.pcap
      - tcp
      - port
      - "1883"

networks:
  iot_net:
    driver: bridge
    internal: true
```
## ~/mosquitto/config/mosquitto.conf
```
listener 1883 0.0.0.0

allow_anonymous true

persistence false

log_dest stdout

connection_messages true

log_type error
log_type warning
log_type notice
log_type information
```
## ~/iot/dispositivo.py
```
import json
import os
import random
import socket
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

BROKER = os.getenv("MQTT_HOST", "mosquitto")
PORT = int(os.getenv("MQTT_PORT", "1883"))

DEVICE_ID = socket.gethostname()
TOPIC = f"laboratorio/iot/{DEVICE_ID}/telemetria"

client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id=DEVICE_ID,
    protocol=mqtt.MQTTv311,
)


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"[{DEVICE_ID}] Error MQTT: {reason_code}", flush=True)
    else:
        print(
            f"[{DEVICE_ID}] Conectado a {BROKER}:{PORT}",
            flush=True,
        )


client.on_connect = on_connect

delay = 10.0
client.reconnect_delay_set(min_delay=1, max_delay=10)

while True:
    try:
        client.connect(BROKER, PORT, keepalive=60)
        break
    except OSError as exc:
        print(f"[{DEVICE_ID}] Broker no disponible: {exc}", flush=True)
        time.sleep(3)

client.loop_start()

try:
    while True:
        payload = {
            "device_id": DEVICE_ID,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "temperature_c": round(random.uniform(18.0, 32.0), 2),
            "humidity_pct": round(random.uniform(30.0, 80.0), 2),
            "battery_pct": random.randint(20, 100),
        }

        try:
            info = client.publish(
                TOPIC,
                json.dumps(payload),
                qos=0,
                retain=False,
            )

            if info.rc == mqtt.MQTT_ERR_SUCCESS:
                print(
                    f"[{DEVICE_ID}] Publicación enviada a {TOPIC}",
                    flush=True,
                )
            else:
                print(
                    f"[{DEVICE_ID}] Error al publicar: {info.rc}",
                    flush=True,
                )

        except (OSError, ValueError) as exc:
            print(f"[{DEVICE_ID}] Error de publicación: {exc}", flush=True)

        time.sleep(delay)

except KeyboardInterrupt:
    pass

finally:
    client.disconnect()
    client.loop_stop()
```
## ~/iot/Dockerfile
```
FROM python:3.12-alpine

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir paho-mqtt==2.1.0

COPY dispositivo.py /app/dispositivo.py

CMD ["python", "-u", "/app/dispositivo.py"]
```
## ~/capturas (empty)