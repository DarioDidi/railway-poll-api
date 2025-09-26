# polls/consumers.py
import json
import os
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poll_site.settings')
User = get_user_model()


class UnifiedConsumer(AsyncWebsocketConsumer):
    """
    Unified WebSocket consumer that handles all real-time subscriptions
    """

    async def connect(self):
        await self.authenticate_user()

        if self.scope["user"].is_authenticated:
            await self.accept()

            # Send connection confirmation
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'data': {'message': 'Connected successfully'}
            }))
        else:
            await self.close(code=4001)

    async def disconnect(self, close_code):
        # Clean up all subscriptions for this connection
        if hasattr(self, 'subscriptions'):
            for channel_name in list(self.subscriptions.keys()):
                await self.unsubscribe_from_channel(channel_name)

    async def receive(self, text_data):
        """Handle messages from WebSocket (subscriptions, etc.)"""
        try:
            message = json.loads(text_data)
            message_type = message.get('type')

            if message_type == 'subscribe':
                await self.handle_subscribe(message)
            elif message_type == 'unsubscribe':
                await self.handle_unsubscribe(message)
            elif message_type == 'vote':
                await self.handle_vote(message)

        except json.JSONDecodeError:
            await self.send_error("Invalid JSON message")

    async def handle_subscribe(self, message):
        """Handle channel subscriptions"""
        channel_name = message.get('channel')

        if not channel_name:
            await self.send_error("Channel name required")
            return

        if not hasattr(self, 'subscriptions'):
            self.subscriptions = {}

        if channel_name not in self.subscriptions:
            await self.subscribe_to_channel(channel_name)
            self.subscriptions[channel_name] = True

            await self.send(text_data=json.dumps({
                'type': 'subscription_confirmed',
                'data': {'channel': channel_name}
            }))

    async def handle_unsubscribe(self, message):
        """Handle channel unsubscriptions"""
        channel_name = message.get('channel')

        if hasattr(self, 'subscriptions') and\
                channel_name in self.subscriptions:
            await self.unsubscribe_from_channel(channel_name)
            del self.subscriptions[channel_name]

    async def subscribe_to_channel(self, channel_name):
        """Subscribe to a specific channel based on its pattern"""
        if channel_name.startswith('poll:'):
            poll_id = channel_name.split(':')[1]
            await self.channel_layer.group_add(
                f'poll_{poll_id}',
                self.channel_name
            )
        elif channel_name == 'polls_list':
            await self.channel_layer.group_add(
                'polls_list',
                self.channel_name
            )
        elif channel_name == 'analytics':
            await self.channel_layer.group_add(
                'analytics',
                self.channel_name
            )

    async def unsubscribe_from_channel(self, channel_name):
        """Unsubscribe from a specific channel"""
        if channel_name.startswith('poll:'):
            poll_id = channel_name.split(':')[1]
            await self.channel_layer.group_discard(
                f'poll_{poll_id}',
                self.channel_name
            )
        elif channel_name == 'polls_list':
            await self.channel_layer.group_discard(
                'polls_list',
                self.channel_name
            )
        elif channel_name == 'analytics':
            await self.channel_layer.group_discard(
                'analytics',
                self.channel_name
            )

    # Generic event handler for all channel messages
    async def channel_event(self, event):
        """Receive events from channel layers and forward to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': event['event_type'],
            'data': event['data'],
            'timestamp': event.get('timestamp')
        }))

    @database_sync_to_async
    def authenticate_user(self):
        """Authenticate user via JWT token"""
        try:
            token = self.scope.get(
                'query_string', b'').decode().split('token=')[1]
            if token:
                import jwt
                from django.conf import settings
                payload = jwt.decode(
                    token, settings.SECRET_KEY, algorithms=['HS256'])
                user = User.objects.get(id=payload['user_id'])
                self.scope["user"] = user
        except (IndexError, jwt.InvalidTokenError,
                User.DoesNotExist, KeyError):
            from django.contrib.auth.models import AnonymousUser
            self.scope["user"] = AnonymousUser()

    async def send_error(self, message):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'data': {'message': message}
        }))
