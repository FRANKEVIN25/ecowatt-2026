import json
import threading
import paho.mqtt.client as mqtt
from django.conf import settings


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[MQTT] Conectado al broker")
        client.subscribe(settings.MQTT_TOPIC)
        print(f"[MQTT] Suscrito a: {settings.MQTT_TOPIC}")
    else:
        print(f"[MQTT] Error de conexión, código: {rc}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        print(f"[MQTT] Mensaje recibido: {payload}")
        guardar_medicion(payload)
    except json.JSONDecodeError as e:
        print(f"[MQTT] Error al parsear JSON: {e}")
    except Exception as e:
        print(f"[MQTT] Error al procesar mensaje: {e}")


def guardar_medicion(payload):
    import django
    from mediciones.models import Medicion

    try:
        medicion = Medicion.objects.create(
            cuarto=payload.get('cuarto', 'principal'),
            voltaje_rms=payload.get('V', 0.0),
            corriente_rms=payload.get('I', 0.0),
            angulo_fase=payload.get('phi', 0.0),
            potencia_activa=payload.get('P', 0.0),
            potencia_reactiva=payload.get('Q', 0.0),
            potencia_aparente=payload.get('S', 0.0),
            factor_potencia=payload.get('fp', 0.0),
            kwh_acumulado=payload.get('kWh', 0.0),
        )
        print(f"[MQTT] Medición guardada: {medicion.id}")
    except Exception as e:
        print(f"[MQTT] Error al guardar en BD: {e}")


def start_mqtt_client():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(
            settings.MQTT_BROKER_HOST,
            settings.MQTT_BROKER_PORT,
            keepalive=60
        )
        thread = threading.Thread(target=client.loop_forever)
        thread.daemon = True
        thread.start()
        print("[MQTT] Cliente iniciado en background")
    except Exception as e:
        print(f"[MQTT] No se pudo conectar al broker: {e}")