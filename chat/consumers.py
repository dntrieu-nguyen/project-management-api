import json
from channels.generic.websocket import AsyncWebsocketConsumer

from app.models import User, Message


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender_id = text_data_json['sender']

        # Lưu tin nhắn vào database
        sender = User.objects.get(id=sender_id)
        room = self.room_name
        message_obj = Message(sender=sender, content=message, room_name=room)
        message_obj.save()

        # Gửi tin nhắn đến group WebSocket
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender.username,
            }
        )

    # Nhận tin nhắn từ group và gửi đến WebSocket
    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']

        # Gửi tin nhắn tới WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
        }))
