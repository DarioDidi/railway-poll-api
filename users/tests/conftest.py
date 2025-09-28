# tests/conftest.py
import pytest
from rest_framework.test import APIClient
from model_bakery import baker
from users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_data():
    return {
        'email': 'test@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'password': 'securepassword123',
        'password_confirm': 'securepassword123'
    }


@pytest.fixture
def create_user(db):
    def make_user(**kwargs):
        return baker.make(User, **kwargs)
    return make_user


@pytest.fixture
def authenticated_user(api_client, create_user):
    user = create_user(
        email='auth@example.com',
        first_name='Auth',
        last_name='User',
        password='testpass123',
        is_active=True
    )
    user.set_password('testpass123')
    user.save()

    # Login the user
    api_client.force_authenticate(user=user)
    return user


@pytest.fixture
def authenticated_client(client, authenticated_user):
    """Authenticated API client"""
    """Create an authenticated client"""
    client = APIClient()
    client.force_authenticate(user=authenticated_user)

    # OR
    # login_success = client.login(email=user.email, password='testpass123')
    # print(f"Login success: {login_success}")

    return client


@pytest.fixture
def unverified_user(create_user):
    user = create_user(
        email='unverified@example.com',
        first_name='Unverified',
        last_name='User',
        password='testpass123',
        is_active=True
    )
    user.set_password('testpass123')
    user.save()
    return user


@pytest.fixture
def inactive_user(create_user):
    user = create_user(
        email='inactive@example.com',
        first_name='Inactive',
        last_name='User',
        password='testpass123',
        is_active=False
    )
    user.set_password('testpass123')
    user.save()
    return user
