import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils.timezone import now
from app.models import Room, Message, User
from asgiref.sync import sync_to_async
import logging

logger = logging.getLogger(__name__)
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"chat_{self.room_name}"

        # join group chat
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # disconnect
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")

        if action == "send_message":
            await self.handle_send_message(data)
        elif action == "load_messages":
            await self.handle_load_messages(data)

    async def handle_send_message(self, data):
        content = data.get("content")
        sender_id = data.get("sender_id")

        # save to db
        message = await sync_to_async(self.save_message)(self.room_name, sender_id, content)

        # send message to all members
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": {
                    "id": str(message.id),
                    "content": message.content,
                    "sender": message.sender.username if message.sender else "Unknown",
                    "created_at": message.created_at.isoformat()
                }
            }
        )

    async def handle_load_messages(self, data):
        offset = data.get("offset", 0)
        limit = data.get("limit", 20)

        # get message from db
        messages = await sync_to_async(self.get_messages)(self.room_name, offset, limit)

        # send previous messsage to client
        await self.send(text_data=json.dumps({
            "action": "load_messages",
            "messages": messages
        }))

    async def chat_message(self, event):
        # send latest message to client
        await self.send(text_data=json.dumps({
            "action": "send_message",
            "message": event["message"]
        }))

    @staticmethod
    def save_message(room_name, sender_id, content):
        room = Room.objects.get(name=room_name)
        sender = None
        if sender_id:
            sender = User.objects.get(id=sender_id)
        return Message.objects.create(room=room, sender=sender, content=content)

    @staticmethod
    def get_messages(room_name, offset, limit):
        try:
            room = Room.objects.get(name=room_name)
        except Room.DoesNotExist:
            return []

        messages = Message.objects.filter(room=room).order_by('-created_at')[offset:offset + limit]
        return [
            {
                "id": str(message.id),
                "content": message.content,
                "sender": message.sender.username if message.sender else "Unknown",
                "created_at": message.created_at.isoformat()
            }
            for message in messages[::-1]
        ]
