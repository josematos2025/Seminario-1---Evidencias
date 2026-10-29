FROM python:3.11-slim

WORKDIR /app

RUN pip install paho-mqtt

COPY simulador_iot_mqtt.py .

CMD ["python", "simulador_iot_mqtt.py"]
