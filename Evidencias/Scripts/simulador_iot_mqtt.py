import time
import random
import json
import os
from datetime import datetime
import paho.mqtt.client as mqtt

BROKER_IP = os.getenv("BROKER_IP", "127.0.0.1")
BROKER_PORT = int(os.getenv("BROKER_PORT", "1883"))

DISPOSITIVOS = [
    {
        "device_id": "camara1",
        "device_type": "camara_ip"
    },
    {
        "device_id": "camara2",
        "device_type": "camara_ip"
    },
    {
        "device_id": "enchufe1",
        "device_type": "enchufe_inteligente"
    }
]

client = mqtt.Client(client_id="simulador_iot_domestico")
client.connect(BROKER_IP, BROKER_PORT, 60)


def generar_datos(dispositivo):
    device_id = dispositivo["device_id"]
    device_type = dispositivo["device_type"]

    if device_type == "camara_ip":
        return {
            "device_id": device_id,
            "device_type": device_type,
            "timestamp": datetime.now().isoformat(),
            "estado": random.choice(["activa", "grabando", "en_espera"]),
            "movimiento_detectado": random.choice([True, False]),
            "bitrate_kbps": random.randint(800, 3000),
            "resolucion": random.choice(["720p", "1080p"]),
            "fps": random.choice([24, 30, 60])
        }

    elif device_type == "enchufe_inteligente":
        return {
            "device_id": device_id,
            "device_type": device_type,
            "timestamp": datetime.now().isoformat(),
            "estado": random.choice(["encendido", "apagado"]),
            "consumo_watts": round(random.uniform(5, 120), 2),
            "voltaje": round(random.uniform(210, 230), 2)
        }


print("[+] Simulador IoT iniciado")
print(f"[+] Broker MQTT: {BROKER_IP}:{BROKER_PORT}")
print("[+] Dispositivos simulados: camara1, camara2, enchufe1")
print("[+] Presiona Ctrl + C para detener")

try:
    while True:
        for dispositivo in DISPOSITIVOS:
            device_id = dispositivo["device_id"]
            device_type = dispositivo["device_type"]

            topic = f"casa/{device_type}/{device_id}/telemetria"
            datos = generar_datos(dispositivo)
            mensaje = json.dumps(datos)

            client.publish(topic, mensaje)
            print(f"Publicado -> {topic}: {mensaje}")

        time.sleep(random.uniform(1, 3))

except KeyboardInterrupt:
    print("\n[!] Simulador detenido")
    client.disconnect()
