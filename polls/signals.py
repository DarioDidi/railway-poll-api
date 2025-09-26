# polls/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Poll, Vote

from django.utils import timezone


# @receiver(post_save, sender=Vote)
# def vote_created(sender, instance, created, **kwargs):
#    """Notify when a new vote is cast"""
#    if created:
#        channel_layer = get_channel_layer()
#
#        # Notify poll-specific subscribers
#        async_to_sync(channel_layer.group_send)(
#            f'poll_{instance.poll.id}',
#            {
#                'type': 'poll_update',
#                'data': {
#                    'type': 'vote_cast',
#                    'poll_id': str(instance.poll.id),
#                    'vote_count': instance.poll.votes.count(),
#                    'timestamp': instance.created_at.isoformat()
#                }
#            }
#        )
#
#        # Notify analytics subscribers
#        async_to_sync(channel_layer.group_send)(
#            'analytics',
#            {
#                'type': 'analytics_update',
#                'data': {
#                    'type': 'new_vote',
#                    'poll_id': str(instance.poll.id),
#                    'timestamp': instance.created_at.isoformat()
#                }
#            }
#        )

@receiver(post_save, sender=Vote)
def vote_created(sender, instance, created, **kwargs):
    """Notify WebSocket clients when a vote is created via API"""
    if created:
        channel_layer = get_channel_layer()

        # Notify poll-specific subscribers
        async_to_sync(channel_layer.group_send)(
            f'poll_{instance.poll.id}',
            {
                'type': 'poll_update',
                'event_type': 'vote_cast',
                'data': {
                    'poll_id': str(instance.poll.id),
                    'total_votes': instance.poll.votes.count(),
                    'option_index': instance.option_index,
                    'timestamp': instance.created_at.isoformat()
                }
            }
        )


@receiver(post_save, sender=Poll)
def poll_created_updated(sender, instance, created, **kwargs):
    """Notify when a poll is created or updated"""
    channel_layer = get_channel_layer()

    if created:
        # Notify all poll list subscribers
        async_to_sync(channel_layer.group_send)(
            'polls_list',
            {
                'type': 'poll_created',
                'data': {
                    'id': str(instance.id),
                    'question': instance.question,
                    'created_at': instance.created_at.isoformat(),
                    'owner_email': instance.owner.email
                }
            }
        )
    else:
        # Notify poll-specific and list subscribers
        async_to_sync(channel_layer.group_send)(
            f'poll_{instance.id}',
            {
                'type': 'poll_update',
                'data': {
                    'type': 'poll_updated',
                    'poll_id': str(instance.id),
                    'changes': ['question', 'options', 'status']  # Simplified
                }
            }
        )


@receiver(post_delete, sender=Poll)
def poll_deleted(sender, instance, **kwargs):
    """Notify when a poll is deleted"""
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        'polls_list',
        {
            'type': 'poll_deleted',
            'data': {
                'id': str(instance.id),
                'timestamp': timezone.now().isoformat()
            }
        }
    )
