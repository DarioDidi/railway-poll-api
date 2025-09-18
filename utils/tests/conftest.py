# conftest.py
import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from polls.models import Poll, Vote, BlockedIP

User = get_user_model()


@pytest.fixture
def client():
    """Regular Django test client"""
    return APIClient()


@pytest.fixture
def user():
    """create a test user"""
    return User.objects.create_user(
        email='test@example.com',
        password='testpass123',
        # first_name='Test',
        # last_name='User'
    )


@pytest.fixture
def user2():
    """Create a second test user"""
    return User.objects.create_user(
        email='test2@example.com',
        password='testpass123',
        # first_name='Test2',
        # last_name='User2'
    )


@pytest.fixture
def authenticated_client(user):
    """Authenticated API client"""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def authenticated_client2(user2):
    """Second authenticated API client"""
    client = APIClient()
    client.force_authenticate(user=user2)
    return client


@pytest.fixture
def poll(user):
    """Create a test poll owned by user"""
    return Poll.objects.create(
        question="Test Poll Question?",
        options=["Option 1", "Option 2", "Option 3"],
        owner=user,
        creator=user,  # Not anonymous
        start_date=timezone.now(),
        expiry_date=timezone.now() + timezone.timedelta(days=1)
    )


@pytest.fixture
def anonymous_poll(user):
    """Create an anonymous test poll owned by user"""
    return Poll.objects.create(
        question="Anonymous Poll Question?",
        options=["Yes", "No"],
        is_anonymous=True,
        owner=user,
        creator=None,  # Anonymous poll
        start_date=timezone.now(),
        expiry_date=timezone.now() + timezone.timedelta(days=1)
    )


@pytest.fixture
def expired_poll(user):
    """Create an expired test poll"""
    return Poll.objects.create(
        question="Expired Poll Question?",
        options=["Choice A", "Choice B"],
        owner=user,
        creator=user,
        start_date=timezone.now() - timezone.timedelta(days=2),
        expiry_date=timezone.now() - timezone.timedelta(days=1)
    )


@pytest.fixture
def future_poll(user):
    """Create a poll that hasn't started yet"""
    start_date = timezone.now() + timezone.timedelta(days=1)
    expiry_date = timezone.now() + timezone.timedelta(days=3)
    return Poll.objects.create(
        question="Future Poll Question?",
        options=["Option X", "Option Y"],
        owner=user,
        creator=user,
        start_date=start_date,
        expiry_date=expiry_date
    )


@pytest.fixture
def poll_with_votes(poll, user):
    """Create a poll with some votes"""
    Vote.objects.create(poll=poll, user=user, option_index=0)
    return poll


@pytest.fixture
def created_vote(poll, user2):
    return Vote.objects.create(poll=poll, user=user2, option_index=1)


@pytest.fixture
def blocked_ip():
    """Create a blocked IP address"""
    return BlockedIP.objects.create(
        ip_address="192.168.1.100",
        reason="Test blocking",
        is_active=True
    )


@pytest.fixture
def mock_request():
    """Create a mock request object for testing middleware"""
    from unittest.mock import Mock
    request = Mock()
    request.META = {}
    return request


@pytest.fixture
def mock_response():
    """Create a mock response object"""
    from unittest.mock import Mock
    response = Mock()
    response.status_code = 200
    return response


@pytest.fixture
def suspicious_request():
    """Create a request that would be considered suspicious"""
    from unittest.mock import Mock
    request = Mock()
    request.META = {
        'REMOTE_ADDR': '192.168.1.100',
        'HTTP_X_FORWARDED_FOR': '192.168.1.100'
    }
    request.path = '/api/auth/login/'
    request.user = None  # Anonymous user
    return request
