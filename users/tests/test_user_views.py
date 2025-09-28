# users/tests/test_views.py
import pytest
from django.urls import reverse
from rest_framework import status
from users.models import User


@pytest.mark.django_db
class TestUserRegistration:
    @pytest.fixture
    def registration_url(self):
        return reverse('register')

    def test_successful_registration(self, api_client,
                                     registration_url, user_data):
        response = api_client.post(registration_url, user_data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['detail'] == 'User registered successfully.'
        assert User.objects.filter(email=user_data['email']).exists()

    def test_registration_duplicate_email(self, api_client, registration_url,
                                          user_data, create_user):
        create_user(email=user_data['email'])

        response = api_client.post(registration_url, user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    def test_registration_invalid_data(self, api_client, registration_url):
        invalid_data = {
            'email': 'invalid-email',
            'first_name': '',
            'last_name': '',
            'password': '123',
            'password_confirm': '123'
        }

        response = api_client.post(registration_url, invalid_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data or 'password' in response.data


@pytest.mark.django_db
class TestUserLogin:
    @pytest.fixture
    def login_url(self):
        return reverse('login')

    def test_successful_login(self, api_client, login_url, create_user):
        user = create_user(
            email='test@example.com',
            password='testpass123',
            # is_active=True
        )
        user.set_password('testpass123')
        user.save()

        login_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }

        response = api_client.post(login_url, login_data)

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert 'user' in response.data

    def test_login_inactive_user(self, api_client, login_url, inactive_user):
        login_data = {
            'email': 'inactive@example.com',
            'password': 'testpass123'
        }

        response = api_client.post(login_url, login_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data

    def test_login_invalid_credentials(self, api_client, login_url):
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        }

        response = api_client.post(login_url, login_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data


@pytest.mark.django_db
class TestUserProfile:
    @pytest.fixture
    def profile_url(self):
        return reverse('user-detail')

    def test_get_profile_authenticated(self, api_client,
                                       profile_url, authenticated_user):
        response = api_client.get(profile_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == authenticated_user.email

    def test_get_profile_unauthenticated(self, api_client, profile_url):
        response = api_client.get(profile_url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile(self, api_client, profile_url, authenticated_user):
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }

        response = api_client.patch(profile_url, update_data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'Updated'
        assert response.data['last_name'] == 'Name'

        authenticated_user.refresh_from_db()
        assert authenticated_user.first_name == 'Updated'


@pytest.mark.django_db
class TestChangePassword:
    @pytest.fixture
    def change_password_url(self):
        return reverse('password-change')

    def test_successful_password_change(
            self, authenticated_client,
            change_password_url, authenticated_user):
        change_data = {
            'current_password': 'testpass123',
            'new_password': 'newsecurepassword456',
            'new_password_confirm': 'newsecurepassword456'
        }

        response = authenticated_client.put(change_password_url, change_data)
        print(f"password change response:{response.data}")

        assert response.status_code == status.HTTP_200_OK
        assert response.data['detail'] == 'Password updated successfully.'

        authenticated_user.refresh_from_db()
        assert authenticated_user.check_password('newsecurepassword456')

    def test_change_password_wrong_current_password(
            self, authenticated_client,
            change_password_url, authenticated_user):
        change_data = {
            'current_password': 'wrongpassword',
            'new_password': 'newsecurepassword456',
            'new_password_confirm': 'newsecurepassword456'
        }

        response = authenticated_client.put(change_password_url, change_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'current_password' in response.data


@pytest.mark.django_db
class TestLogout:
    @pytest.fixture
    def logout_url(self):
        return reverse('logout')

    def test_successful_logout(
            self, api_client, logout_url, authenticated_user):
        response = api_client.post(logout_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['detail'] == 'Successfully logged out.'
