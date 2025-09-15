import pytest
from django.utils import timezone
from polls.models import Poll
from users.models import User


@pytest.mark.django_db
class TestPollModel:
    """Test cases for Poll model"""

    def test_create_poll_with_owner(self, user):
        """Test creating a poll with owner and creator"""
        poll = Poll.objects.create(
            question="Test Poll Question?",
            options=["Option 1", "Option 2", "Option 3"],
            owner=user,
            creator=user,
            start_date=timezone.now(),
            expiry_date=timezone.now() + timezone.timedelta(days=1)
        )

        assert poll.owner == user
        assert poll.creator == user
        assert poll.is_anonymous is False

    def test_create_anonymous_poll(self, user):
        """Test creating an anonymous poll"""
        poll = Poll.objects.create(
            question="Anonymous Poll",
            options=["Yes", "No"],
            is_anonymous=True,
            owner=user,
            creator=None,
            start_date=timezone.now(),
            expiry_date=timezone.now() + timezone.timedelta(days=1)
        )

        assert poll.owner == user
        assert poll.creator is None
        assert poll.is_anonymous is True

    def test_poll_can_vote_status(self, user):
        """Test poll voting status calculations"""
        now = timezone.now()

        # Active poll
        active_poll = Poll.objects.create(
            question="Active Poll",
            options=["Yes", "No"],
            owner=user,
            creator=user,
            start_date=now - timezone.timedelta(hours=1),
            expiry_date=now + timezone.timedelta(hours=23)
        )

        # Expired poll
        expired_poll = Poll.objects.create(
            question="Expired Poll",
            options=["Yes", "No"],
            owner=user,
            creator=user,
            start_date=now - timezone.timedelta(days=2),
            expiry_date=now - timezone.timedelta(days=1)
        )

        # Future poll
        future_poll = Poll.objects.create(
            question="Future Poll",
            options=["Yes", "No"],
            owner=user,
            creator=user,
            start_date=now + timezone.timedelta(hours=1),
            expiry_date=now + timezone.timedelta(days=1)
        )

        assert active_poll.can_vote() is True
        assert expired_poll.can_vote() is False
        assert future_poll.can_vote() is False
