import pytest
from django.utils import timezone
from polls.models import Poll, Vote, BlockedIP


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


@pytest.mark.django_db
class TestVoteModel:
    """Test cases for Vote model"""

    def test_create_vote(self, poll, user):
        vote = Vote.objects.create(poll=poll, user=user, option_index=0)

        assert vote.poll == poll
        assert vote.user == user
        assert vote.option_index == 0

    def test_unique_vote_constraint(self, poll, user):
        """Test that a user can only vote once per poll"""
        Vote.objects.create(poll=poll, user=user, option_index=0)

        # Attempting to create another vote should raise
        # IntegrityError or ValidationError
        with pytest.raises(Exception):
            Vote.objects.create(poll=poll, user=user, option_index=1)

    def test_vote_save_prevents_updates(self, user, poll):
        """Test that votes cannot be updated after creation"""
        vote = Vote.objects.create(
            poll=poll,
            user=user,
            option_index=0
        )

        vote.refresh_from_db()
        vote.option_index = 1
        with pytest.raises(PermissionError, match="Votes cannot be modified"):
            vote.save()

    def test_vote_delete_prevents_deletion(self, user, poll):
        """Test that votes cannot be deleted"""
        vote = Vote.objects.create(
            poll=poll,
            user=user,
            option_index=0
        )

        # Attempt to delete the vote
        with pytest.raises(PermissionError, match="Votes cannot be deleted"):
            vote.delete()


@pytest.mark.django_db
class TestBlockedIPModel:
    """Test cases for BlockedIP model"""

    def test_create_blocked_ip(self):
        """Test creating a blocked IP entry"""
        blocked_ip = BlockedIP.objects.create(
            ip_address="192.168.1.100",
            reason="Test blocking",
            is_active=True
        )

        assert blocked_ip.ip_address == "192.168.1.100"
        assert blocked_ip.reason == "Test blocking"
        assert blocked_ip.is_active is True
