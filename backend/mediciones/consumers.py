import json
from channels.generic.websocket import AsyncWebsocketConsumer


class MedicionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(
            "mediciones",
            self.channel_name
        )
        await self.accept()
        print("[WS] Cliente conectado")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "mediciones",
            self.channel_name
        )
        print("[WS] Cliente desconectado")

    async def medicion_update(self, event):
        await self.send(text_data=json.dumps(event["data"]))