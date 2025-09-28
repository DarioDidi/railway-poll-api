# conftest.py
import pytest
from users.models import User
from rest_framework.test import APIClient


@pytest.fixture
def user():
    """Create a test user with verified email"""
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123',
    )
    return user


@pytest.fixture
def verified_user():
    """Create a test user with verified email"""
    user = User.objects.create_user(
        email='verified@example.com',
        password='testpass123',
    )

    return user


@pytest.fixture
def unverified_user():
    """Create a test user with unverified email"""
    user = User.objects.create_user(
        email='unverified@example.com',
        password='testpass123',
        # email_verified=False
    )
    return user


@pytest.fixture
def authenticated_client(client, verified_user):
    """Authenticated API client"""
    """Create an authenticated client"""
    client = APIClient()
    # Try both authentication methods:

    # Method 1: Using force_authenticate (recommended for tests)
    client.force_authenticate(user=verified_user)

    # OR Method 2: Using login (if you need session auth)
    # login_success = client.login(email=user.email, password='testpass123')
    # print(f"Login success: {login_success}")

    return client
