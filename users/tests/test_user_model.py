# users/tests/test_user_models.py
import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Test cases for Custom User Model"""

    def test_create_user(self):
        """Test creating a regular user"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
        )

        assert user.email == 'test@example.com'
        assert user.check_password('testpass123')
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.email_verified is False

    def test_create_superuser(self):
        """Test creating a superuser"""
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            # username='super1'
        )

        assert superuser.email == 'admin@example.com'
        assert superuser.is_staff is True
        assert superuser.is_superuser is True

    def test_user_str_representation(self):
        """Test user string representation"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        assert str(user) == 'test@example.com'

    def test_unique_email_constraint(self):
        """Test that email addresses must be unique
            Emails are case insensitive
        """
        User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

        with pytest.raises(Exception):
            User.objects.create_user(
                email='Test@example.com',
                password='anotherpass123'
            )

    def test_email_normalization(self):
        """Test that email is normalized to lowercase"""
        user = User.objects.create_user(
            email='Test@Example.COM',
            password='testpass123'
        )
        assert user.email == 'test@example.com'

    def test_user_without_email(self):
        """Test that email is required"""
        with pytest.raises(ValueError):
            User.objects.create_user(
                email=None,
                password='testpass123'
            )

    def test_create_user_with_extra_fields(self):
        """Test creating user with additional fields"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            email_verified=True
        )

        assert user.email_verified is True
