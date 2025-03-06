import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, Message, PrivateChat, PrivateMessage
from django.contrib.auth.models import User

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        username = data.get('username')
        message = data.get('message')
        if not message.strip():
            return

        user = await self.get_user(username)
        room = await self.get_room(self.room_name)
        msg = await self.create_message(user, room, message)
        timestamp = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'username': username,
                'message': message,
                'timestamp': timestamp,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def get_user(self, username):
        user, _ = User.objects.get_or_create(username=username)
        return user

    @database_sync_to_async
    def get_room(self, room_name):
        room, _ = ChatRoom.objects.get_or_create(name=room_name)
        return room

    @database_sync_to_async
    def create_message(self, user, room, message):
        return Message.objects.create(user=user, room=room, content=message)



class PrivateChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'private_chat_{self.chat_id}'
        # Add the user to the private chat group:
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        sender_username = data.get('sender')
        content = data.get('content')
        # Save the message to the database:
        message = await self.save_message(sender_username, content)
        timestamp = message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # Broadcast the message to the group:
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'private_message',
                'sender': sender_username,
                'content': content,
                'timestamp': timestamp,
            }
        )

    async def private_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def save_message(self, sender_username, content):
        # Get the sender user and chat
        sender = User.objects.get(username=sender_username)
        chat = PrivateChat.objects.get(id=self.chat_id)
        return PrivateMessage.objects.create(chat=chat, sender=sender, content=content)
