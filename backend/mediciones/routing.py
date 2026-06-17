from django.urls import re_path
from mediciones.consumers import MedicionConsumer

websocket_urlpatterns = [
    re_path(r'ws/mediciones/$', MedicionConsumer.as_asgi()),
]