from django.apps import AppConfig


class MedicionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mediciones'

    def ready(self):
        from mediciones.mqtt_client import start_mqtt_client
        import threading
        threading.Thread(target=start_mqtt_client, daemon=True).start()