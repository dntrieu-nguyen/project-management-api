import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils.timezone import now
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from app.models import Room, Message, User
import logging

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        ###########################################
        Main flow of websocket
        ###########################################
        """
        try:
            # Get token or sender_id from query string
            sender_id = self.scope['query_string'].decode().split('id=')[1]
            
            self.room_name = self.scope['url_route']['kwargs']['room_name']
            self.room_group_name = f"chat_{self.room_name}"

            # Create or fetch room
            self.room = await database_sync_to_async(self.get_or_create_room)(self.room_name)

            # Add sender as a member of the room
            await self.add_user_to_room(sender_id)

            # Join group chat
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()

            logger.info(f"User {sender_id} connected to room {self.room_name}")

        except Exception as e:
            logger.error(f"Error during websocket connect: {e}")
            await self.close()

    async def disconnect(self, close_code):
        try:
            # Leave the group chat
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        except Exception as e:
            logger.error(f"Error during websocket disconnect: {e}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get("action")

            if action == "send_message":
                await self.handle_send_message(data)
            elif action == "load_messages":
                await self.handle_load_messages(data)

        except Exception as e:
            logger.error(f"Error in receive method: {e}")
            await self.send(text_data=json.dumps({
                "error": "Invalid data format or internal error"
            }))

    async def handle_send_message(self, data):
        try:
            content = data.get("content")
            sender_id = data.get("sender_id")

            # Save to db
            message = await sync_to_async(self.save_message)(self.room_name, sender_id, content)

            # send message to all members in group
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
        except Exception as e:
            logger.error(f"Error in handle_send_message: {e}")

    async def handle_load_messages(self, data):
        try:
            offset = data.get("offset", 0)
            limit = data.get("limit", 20)

            # get message from db
            messages = await sync_to_async(self.get_messages)(self.room_name, offset, limit)

            # Send messages to client
            await self.send(text_data=json.dumps({
                "action": "load_messages",
                "messages": messages
            }))
        except Exception as e:
            logger.error(f"Error in handle_load_messages: {e}")

    async def chat_message(self, event):
        try:
            # Send message to WebSocket
            await self.send(text_data=json.dumps({
                "action": "send_message",
                "message": event["message"]
            }))
        except Exception as e:
            logger.error(f"Error in chat_message: {e}")

    async def add_user_to_room(self, user_id):
        try:
            # get user from db
            user = await database_sync_to_async(User.objects.get)(id=user_id)

            # save user to room
            if user not in await database_sync_to_async(lambda: list(self.room.members.all()))():
                await database_sync_to_async(self.room.members.add)(user)
                await database_sync_to_async(self.room.save)()
            
            logger.info(f"User {user_id} added to room {self.room_name}")
            
        except Exception as e:
            logger.error(f"Error in add_user_to_room: {e}")

    """
    ###########################################
    Helper Methods
    ###########################################
    """
    @staticmethod
    def save_message(room_name, sender_id, content):
        room = Room.objects.get(name=room_name)
        sender = User.objects.get(id=sender_id) if sender_id else None
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

    @staticmethod
    def get_or_create_room(room_name):
        room, created = Room.objects.get_or_create(name=room_name)
        return room

print(f'chat_userid_uuid')