# tests/test_serializers.py
import pytest
from django.contrib.auth import get_user_model
from users.serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    #   PasswordResetRequestSerializer,
    #   PasswordResetConfirmSerializer
)
# from model_bakery import baker

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistrationSerializer:
    def test_valid_registration_data(self, db):
        data = {
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'password': 'securepassword123',
            'password_confirm': 'securepassword123'
        }

        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid()

    def test_password_mismatch(self, db):
        data = {
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'password': 'securepassword123',
            'password_confirm': 'differentpassword'
        }

        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password_confirm' in serializer.errors

    def test_weak_password(self, db):
        data = {
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'password': '123',
            'password_confirm': '123'
        }

        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors

    def test_duplicate_email(self, db, create_user):
        create_user(email='existing@example.com')

        data = {
            'email': 'existing@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'password': 'securepassword123',
            'password_confirm': 'securepassword123'
        }

        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors

    def test_create_user(self, db):
        data = {
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'password': 'securepassword123',
            'password_confirm': 'securepassword123'
        }

        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid()

        user = serializer.save()
        assert user.email == 'test@example.com'
        assert user.check_password('securepassword123')
        assert user.username is not None


@pytest.mark.django_db
class TestUserLoginSerializer:
    def test_valid_login(self, create_user, rf):
        user = create_user(
            email='test@example.com',
            password='testpass123',
            email_verified=True,
            is_active=True
        )
        user.set_password('testpass123')
        user.save()

        request = rf.post('/login/')
        serializer = UserLoginSerializer(
            data={'email': 'test@example.com', 'password': 'testpass123'},
            context={'request': request}
        )

        assert serializer.is_valid()
        assert serializer.validated_data['user'] == user

    def test_invalid_credentials(self, rf):
        request = rf.post('/login/')
        serializer = UserLoginSerializer(
            data={'email': 'nonexistent@example.com', 'password': 'wrongpass'},
            context={'request': request}
        )

        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors

    def test_unverified_email(self, create_user, rf):
        user = create_user(
            email='test@example.com',
            password='testpass123',
            email_verified=False,
            is_active=True
        )
        user.set_password('testpass123')
        user.save()

        request = rf.post('/login/')
        serializer = UserLoginSerializer(
            data={'email': 'test@example.com', 'password': 'testpass123'},
            context={'request': request}
        )

        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors

    def test_inactive_user(self, create_user, rf):
        user = create_user(
            email='test@example.com',
            password='testpass123',
            email_verified=True,
            is_active=False
        )
        user.set_password('testpass123')
        user.save()

        request = rf.post('/login/')
        serializer = UserLoginSerializer(
            data={'email': 'test@example.com', 'password': 'testpass123'},
            context={'request': request}
        )

        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors


@pytest.mark.django_db
class TestUserProfileSerializer:
    def test_serialize_user(self, create_user):
        user = create_user(
            email='test@example.com',
            first_name='John',
            last_name='Doe'
        )

        serializer = UserProfileSerializer(user)
        data = serializer.data

        assert data['email'] == 'test@example.com'
        assert data['first_name'] == 'John'
        assert data['last_name'] == 'Doe'
        assert 'full_name' in data

    def test_update_user_profile(self, create_user):
        user = create_user(
            email='test@example.com',
            first_name='John',
            last_name='Doe'
        )

        serializer = UserProfileSerializer(
            user,
            data={'first_name': 'Jane', 'last_name': 'Smith'},
            partial=True
        )

        assert serializer.is_valid()
        updated_user = serializer.save()
        assert updated_user.first_name == 'Jane'
        assert updated_user.last_name == 'Smith'


@pytest.mark.django_db
class TestChangePasswordSerializer:
    def test_valid_password_change(self, authenticated_user, rf):
        request = rf.post('/change-password/')
        request.user = authenticated_user

        data = {
            'current_password': 'testpass123',
            'new_password': 'newsecurepassword456',
            'new_password_confirm': 'newsecurepassword456'
        }

        serializer = ChangePasswordSerializer(
            data=data, context={'request': request})
        assert serializer.is_valid()

    def test_wrong_current_password(self, authenticated_user, rf):
        request = rf.post('/change-password/')
        request.user = authenticated_user

        data = {
            'current_password': 'wrongpassword',
            'new_password': 'newsecurepassword456',
            'new_password_confirm': 'newsecurepassword456'
        }

        serializer = ChangePasswordSerializer(
            data=data, context={'request': request})
        assert not serializer.is_valid()
        assert 'current_password' in serializer.errors

    def test_password_mismatch(self, authenticated_user, rf):
        request = rf.post('/change-password/')
        request.user = authenticated_user

        data = {
            'current_password': 'testpass123',
            'new_password': 'newsecurepassword456',
            'new_password_confirm': 'differentpassword'
        }

        serializer = ChangePasswordSerializer(
            data=data, context={'request': request})
        assert not serializer.is_valid()
        assert 'new_password_confirm' in serializer.errors
