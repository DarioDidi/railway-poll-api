# polls/consumers.py
# import json
# import jwt
# from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.db import database_sync_to_async
#
# from django.conf import settings
# from django.contrib.auth import get_user_model
# from django.contrib.auth.models import AnonymousUser
# from django.utils import timezone
#
#
# from .models import Poll, Vote
# User = get_user_model()
#
#
# class PollConsumer(AsyncWebsocketConsumer):
#    """
#    WebSocket consumer for real-time poll updates.
#    Handles subscriptions to poll-specific updates.
#    """
#
#    async def connect(self):
#        self.poll_id = self.scope['url_route']['kwargs']['poll_id']
#        self.poll_group_name = f'poll_{self.poll_id}'
#
#        # Authenticate user via JWT from query string
#        await self.authenticate_user()
#
#        if self.scope["user"].is_authenticated:
#            # Join poll group
#            await self.channel_layer.group_add(
#                self.poll_group_name,
#                self.channel_name
#            )
#            await self.accept()
#
#            # Send current poll state
#            poll_data = await self.get_poll_data()
#            await self.send(text_data=json.dumps({
#                'type': 'poll_data',
#                'data': poll_data
#            }))
#        else:
#            await self.close(code=4001)  # Unauthorized
#
#    async def disconnect(self, close_code):
#        # Leave poll group
#        if hasattr(self, 'poll_group_name'):
#            await self.channel_layer.group_discard(
#                self.poll_group_name,
#                self.channel_name
#            )
#
#    async def receive(self, text_data):
#        """Handle messages from WebSocket (e.g., voting)"""
#        text_data_json = json.loads(text_data)
#        message_type = text_data_json['type']
#
#        if message_type == 'vote':
#            await self.handle_vote(text_data_json['option_index'])
#
#    async def handle_vote(self, option_index):
#        """Process a vote from WebSocket"""
#        user = self.scope["user"]
#        success, message = await self.cast_vote(user, option_index)
#
#        if success:
#            # Broadcast updated results to all subscribers
#            results = await self.get_poll_results()
#            await self.channel_layer.group_send(
#                self.poll_group_name,
#                {
#                    'type': 'poll_update',
#                    'data': {
#                        'type': 'vote_cast',
#                        'results': results,
#                        'timestamp': timezone.now().isoformat()
#                    }
#                }
#            )
#
#        await self.send(text_data=json.dumps({
#            'type': 'vote_response',
#            'success': success,
#            'message': message
#        }))
#
#    async def poll_update(self, event):
#        """Send poll updates to WebSocket"""
#        await self.send(text_data=json.dumps(event['data']))
#
#    @database_sync_to_async
#    def authenticate_user(self):
#        """Authenticate user via JWT token from query string"""
#        try:
#            token = self.scope['query_string'].decode().split('token=')[1]
#            if token:
#                payload = jwt.decode(
#                    token, settings.SECRET_KEY, algorithms=['HS256'])
#                user = User.objects.get(id=payload['user_id'])
#                self.scope["user"] = user
#        except (IndexError, jwt.InvalidTokenError,
#                User.DoesNotExist, KeyError):
#            self.scope["user"] = AnonymousUser()
#
#    @database_sync_to_async
#    def get_poll_data(self):
#        """Get current poll data"""
#        try:
#            poll = Poll.objects.get(id=self.poll_id)
#            return {
#                'id': str(poll.id),
#                'question': poll.question,
#                'options': poll.options,
#                'total_votes': poll.votes.count(),
#                'has_ended': poll.has_ended,
#                'can_vote': poll.can_vote(),
#                'results': self.get_poll_results_sync(poll)
#            }
#        except Poll.DoesNotExist:
#            return None
#
#    @database_sync_to_async
#    def get_poll_results(self):
#        """Get current poll results"""
#        try:
#            poll = Poll.objects.get(id=self.poll_id)
#            return self.get_poll_results_sync(poll)
#        except Poll.DoesNotExist:
#            return []
#
#    def get_poll_results_sync(self, poll):
#        """Sync method to get poll results"""
#        results = []
#        for index, option in enumerate(poll.options):
#            vote_count = poll.votes.filter(option_index=index).count()
#            total_votes = poll.votes.count()
#            percentage = (vote_count / total_votes *
#                          100) if total_votes > 0 else 0
#
#            results.append({
#                'option': option,
#                'votes': vote_count,
#                'percentage': round(percentage, 2)
#            })
#        return results
#
#    @database_sync_to_async
#    def cast_vote(self, user, option_index):
#        """Cast a vote for the user"""
#        try:
#            poll = Poll.objects.get(id=self.poll_id)
#
#            # Check if user can vote
#            if not poll.can_vote():
#                return False, "Poll is not active"
#
#            # Check if user already voted
#            if Vote.objects.filter(poll=poll, user=user).exists():
#                return False, "You have already voted on this poll"
#
#            # Create vote
#            Vote.objects.create(poll=poll, user=user,
#                                option_index=option_index)
#            return True, "Vote cast successfully"
#
#        except Poll.DoesNotExist:
#            return False, "Poll not found"
#        except Exception as e:
#            return False, str(e)
#
#
# class PollListConsumer(AsyncWebsocketConsumer):
#    """
#    WebSocket consumer for real-time poll list updates.
#    Handles notifications for poll creation, deletion, and updates.
#    """
#
#    async def connect(self):
#        await self.authenticate_user()
#
#        if self.scope["user"].is_authenticated:
#            self.user_group_name = f'user_{self.scope["user"].id}'
#            self.polls_group_name = 'polls_list'
#
#            # Join user-specific and global polls groups
#            await self.channel_layer.group_add(
#                self.user_group_name,
#                self.channel_name
#            )
#            await self.channel_layer.group_add(
#                self.polls_group_name,
#                self.channel_name
#            )
#            await self.accept()
#        else:
#            await self.close(code=4001)
#
#    async def disconnect(self, close_code):
#        if hasattr(self, 'user_group_name'):
#            await self.channel_layer.group_discard(
#                self.user_group_name,
#                self.channel_name
#            )
#        if hasattr(self, 'polls_group_name'):
#            await self.channel_layer.group_discard(
#                self.polls_group_name,
#                self.channel_name
#            )
#
#    async def poll_created(self, event):
#        """Send poll creation notification"""
#        await self.send(text_data=json.dumps({
#            'type': 'poll_created',
#            'data': event['data']
#        }))
#
#    async def poll_updated(self, event):
#        """Send poll update notification"""
#        await self.send(text_data=json.dumps({
#            'type': 'poll_updated',
#            'data': event['data']
#        }))
#
#    async def poll_deleted(self, event):
#        """Send poll deletion notification"""
#        await self.send(text_data=json.dumps({
#            'type': 'poll_deleted',
#            'data': event['data']
#        }))
#
#    @database_sync_to_async
#    def authenticate_user(self):
#        """Authenticate user via JWT token"""
#        try:
#            token = self.scope['query_string'].decode().split('token=')[1]
#            if token:
#                payload = jwt.decode(
#                    token, settings.SECRET_KEY, algorithms=['HS256'])
#                user = User.objects.get(id=payload['user_id'])
#                self.scope["user"] = user
#        except (IndexError, jwt.InvalidTokenError,
#                User.DoesNotExist, KeyError):
#            self.scope["user"] = AnonymousUser()


# polls/consumers.py (updated)
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

        if hasattr(self, 'subscriptions') and channel_name in self.subscriptions:
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

    async def handle_vote(self, message):
        """Handle voting through WebSocket"""
        poll_id = message.get('poll_id')
        option_index = message.get('option_index')
        user = self.scope["user"]

        success, result = await self.cast_vote(user, poll_id, option_index)

        await self.send(text_data=json.dumps({
            'type': 'vote_response',
            'data': {
                'success': success,
                'result': result,
                'poll_id': poll_id
            }
        }))

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
        except (IndexError, jwt.InvalidTokenError, User.DoesNotExist, KeyError):
            from django.contrib.auth.models import AnonymousUser
            self.scope["user"] = AnonymousUser()

    @database_sync_to_async
    def cast_vote(self, user, poll_id, option_index):
        """Cast a vote (same logic as your API view)"""
        from .models import Poll, Vote
        try:
            poll = Poll.objects.get(id=poll_id)

            if not poll.can_vote():
                return False, "Poll is not active"

            if Vote.objects.filter(poll=poll, user=user).exists():
                return False, "You have already voted on this poll"

            Vote.objects.create(poll=poll, user=user,
                                option_index=option_index)
            return True, "Vote cast successfully"

        except Poll.DoesNotExist:
            return False, "Poll not found"
        except Exception as e:
            return False, str(e)

    async def send_error(self, message):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'data': {'message': message}
        }))
