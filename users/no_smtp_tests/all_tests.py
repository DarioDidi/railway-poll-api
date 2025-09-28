# tests/test_registration.py
from users.utils import (
    generate_reset_code, store_reset_code, verify_reset_code, clear_reset_code)
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
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
        assert response.data['detail'] == (
            'User registered successfully.')
        assert 'user_id' in response.data

        # Verify user was created
        user = User.objects.get(email=user_data['email'])
        assert user.check_password(user_data['password'])
        assert user.is_active is True

    def test_registration_duplicate_email(self, api_client, registration_url,
                                          user_data, create_user):
        create_user(email=user_data['email'])

        response = api_client.post(registration_url, user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    def test_registration_password_mismatch(
            self, api_client, registration_url):
        invalid_data = {
            'email': 'test@example.com',
            'password': 'tryusing234new',
            'password_confirm': 'tryusing456old'
        }

        response = api_client.post(registration_url, invalid_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password_confirm' in response.data

    def test_registration_weak_password(self, api_client, registration_url):
        weak_password_data = {
            'email': 'test@example.com',
            'password': '123',
            'password_confirm': '123'
        }

        response = api_client.post(registration_url, weak_password_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data

    def test_registration_missing_required_fields(self, api_client,
                                                  registration_url):
        incomplete_data = {
            'email': 'test@example.com',
            # missing first_name, last_name, etc.
        }

        response = api_client.post(registration_url, incomplete_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

# tests/test_login.py


@pytest.mark.django_db
class TestUserLogin:
    @pytest.fixture
    def login_url(self):
        return reverse('login')

    def test_successful_login(self, api_client, login_url, create_user):
        user = create_user(
            email='test@example.com',
            password='testpass123',
            is_active=True
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
        assert response.data['user']['email'] == 'test@example.com'

    def test_login_inactive_user(self, api_client, login_url, inactive_user):
        login_data = {
            'email': 'inactive@example.com',
            'password': 'testpass123'
        }

        response = api_client.post(login_url, login_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data

    def test_login_invalid_credentials(self, api_client,
                                       login_url, create_user):
        user = create_user(
            email='test@example.com',
            password='testpass123',
            is_active=True
        )
        user.set_password('testpass123')
        user.save()

        login_data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }

        response = api_client.post(login_url, login_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data

    def test_login_nonexistent_user(self, api_client, login_url):
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'somepassword'
        }

        response = api_client.post(login_url, login_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data

# tests/test_password_reset.py


@pytest.mark.django_db
class TestPasswordReset:
    @pytest.fixture
    def reset_request_url(self):
        return reverse('password-reset-request')

    @pytest.fixture
    def reset_confirm_url(self):
        return reverse('password-reset-confirm')

    def test_password_reset_request_success(self, api_client,
                                            reset_request_url, create_user):
        create_user(email='test@example.com', is_active=True)

        response = api_client.post(
            reset_request_url, {'email': 'test@example.com'})

        assert response.status_code == status.HTTP_200_OK
        assert 'reset_code' in response.data
        assert response.data['email'] == 'test@example.com'
        assert response.data['expires_in'] == 900

        # Verify code is stored in cache
        cache_key = "password_reset_test@example.com"
        stored_code = cache.get(cache_key)
        assert stored_code == response.data['reset_code']

    def test_password_reset_request_nonexistent_user(self,
                                                     api_client,
                                                     reset_request_url):
        response = api_client.post(
            reset_request_url, {'email': 'nonexistent@example.com'})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    def test_password_reset_request_inactive_user(
            self, api_client, reset_request_url, inactive_user):
        response = api_client.post(
            reset_request_url, {'email': 'inactive@example.com'})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    def test_password_reset_confirm_success(
            self, api_client, reset_confirm_url,
            create_user, reset_request_url):
        user = create_user(email='test@example.com', is_active=True)
        user.set_password('oldpassword')
        user.save()

        # First request reset code
        reset_response = api_client.post(
            reset_request_url, {'email': 'test@example.com'})
        reset_code = reset_response.data['reset_code']

        # Confirm reset with new password
        confirm_data = {
            'email': 'test@example.com',
            'reset_code': reset_code,
            'new_password': 'newsecurepassword456',
            'new_password_confirm': 'newsecurepassword456'
        }

        response = api_client.post(reset_confirm_url, confirm_data)

        print(f"reset_confirm response:{response}")
        print(f"reset_confirm response:{response.data}")
        assert response.status_code == status.HTTP_200_OK
        assert response.data['detail'] == 'Password reset successfully.'

        # Verify password was changed
        user.refresh_from_db()
        assert user.check_password('newsecurepassword456')

        # Verify code was cleared from cache
        cache_key = "password_reset_test@example.com"
        assert cache.get(cache_key) is None

    def test_password_reset_confirm_invalid_code(
            self, api_client, reset_confirm_url, create_user):
        create_user(email='test@example.com', is_active=True)

        confirm_data = {
            'email': 'test@example.com',
            'reset_code': 'invalidcode',
            'new_password': 'newsecurepassword456',
            'new_password_confirm': 'newsecurepassword456'
        }

        response = api_client.post(reset_confirm_url, confirm_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'detail' in response.data
        assert 'Invalid or expired reset code' in response.data['detail']

    def test_password_reset_confirm_password_mismatch(
            self, api_client, reset_request_url,
            reset_confirm_url, create_user):
        create_user(email='test@example.com', is_active=True)
        reset_response = api_client.post(
            reset_request_url, {'email': 'test@example.com'})
        reset_code = reset_response.data['reset_code']

        confirm_data = {
            'email': 'test@example.com',
            'reset_code': reset_code,
            'new_password': 'tryusing234new',
            'new_password_confirm': 'tryusing456old'
        }

        response = api_client.post(reset_confirm_url, confirm_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'new_password_confirm' in response.data

    def test_password_reset_confirm_nonexistent_user(self, api_client,
                                                     reset_confirm_url):
        confirm_data = {
            'email': 'nonexistent@example.com',
            'reset_code': '123456',
            'new_password': 'newsecurepassword456',
            'new_password_confirm': 'newsecurepassword456'
        }

        response = api_client.post(reset_confirm_url, confirm_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'detail' in response.data

# tests/test_password_change.py


@pytest.mark.django_db
class TestPasswordChange:
    @pytest.fixture
    def change_password_url(self):
        return reverse('password-change')

    def test_successful_password_change(self, api_client, change_password_url,
                                        authenticated_user):
        change_data = {
            'current_password': 'testpass123',
            'new_password': 'newsecurepassword456',
            'new_password_confirm': 'newsecurepassword456'
        }

        response = api_client.put(change_password_url, change_data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['detail'] == 'Password updated successfully.'

        authenticated_user.refresh_from_db()
        assert authenticated_user.check_password('newsecurepassword456')

    def test_password_change_wrong_current_password(self, api_client,
                                                    change_password_url,
                                                    authenticated_user):
        change_data = {
            'current_password': 'wrongpassword',
            'new_password': 'newsecurepassword456',
            'new_password_confirm': 'newsecurepassword456'
        }

        response = api_client.put(change_password_url, change_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'current_password' in response.data

    def test_password_change_unauthenticated(self, api_client,
                                             change_password_url):
        change_data = {
            'current_password': 'testpass123',
            'new_password': 'newsecurepassword456',
            'new_password_confirm': 'newsecurepassword456'
        }

        response = api_client.put(change_password_url, change_data)

        assert response.status_code in [status.HTTP_403_FORBIDDEN,
                                        status.HTTP_401_UNAUTHORIZED]

    def test_password_change_weak_new_password(self, api_client,
                                               change_password_url,
                                               authenticated_user):
        change_data = {
            'current_password': 'testpass123',
            'new_password': '123',
            'new_password_confirm': '123'
        }

        response = api_client.put(change_password_url, change_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'new_password' in response.data


# tests/test_profile.py


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
        assert response.data['first_name'] == authenticated_user.first_name
        assert response.data['last_name'] == authenticated_user.last_name
        assert 'id' in response.data

    def test_get_profile_unauthenticated(self, api_client, profile_url):
        response = api_client.get(profile_url)

        assert response.status_code in [status.HTTP_403_FORBIDDEN,
                                        status.HTTP_401_UNAUTHORIZED]

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
        assert authenticated_user.last_name == 'Name'

    def test_update_profile_email_not_allowed(self, api_client,
                                              profile_url, authenticated_user):
        update_data = {
            'email': 'newemail@example.com'
        }

        response = api_client.patch(profile_url, update_data)

        # Email should remain unchanged (read-only field)
        assert response.data['email'] == authenticated_user.email
        authenticated_user.refresh_from_db()
        assert authenticated_user.email == 'auth@example.com'


# tests/test_logout.py


@pytest.mark.django_db
class TestUserLogout:
    @pytest.fixture
    def logout_url(self):
        return reverse('logout')

    def test_successful_logout(self, api_client,
                               logout_url, authenticated_user):
        response = api_client.post(logout_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['detail'] == 'Successfully logged out.'

    def test_logout_unauthenticated(self, api_client, logout_url):
        response = api_client.post(logout_url)

        assert response.status_code in [status.HTTP_403_FORBIDDEN,
                                        status.HTTP_401_UNAUTHORIZED]


# tests/test_tokens.py


@pytest.mark.django_db
class TestTokenEndpoints:
    @pytest.fixture
    def token_verify_url(self):
        return reverse('token-verify')

    @pytest.fixture
    def token_refresh_url(self):
        return reverse('token-refresh')

    def test_token_verify_valid(self, api_client,
                                token_verify_url, create_user):
        user = create_user(email='test@example.com')
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        response = api_client.post(token_verify_url, {'token': access_token})

        assert response.status_code == status.HTTP_200_OK

    def test_token_verify_invalid(self, api_client, token_verify_url):
        response = api_client.post(token_verify_url, {'token': 'invalidtoken'})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_refresh_valid(self, api_client,
                                 token_refresh_url, create_user):
        user = create_user(email='test@example.com')
        refresh = RefreshToken.for_user(user)

        response = api_client.post(
            token_refresh_url, {'refresh': str(refresh)})

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data

    def test_token_refresh_invalid(self, api_client, token_refresh_url):
        response = api_client.post(
            token_refresh_url, {'refresh': 'invalidrefreshtoken'})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

# tests/test_utils.py


@pytest.mark.django_db
class TestPasswordResetUtils:
    def test_generate_reset_code(self):
        code = generate_reset_code()

        assert len(code) == 6
        assert code.isdigit()

    def test_store_and_verify_reset_code(self):
        email = 'test@example.com'
        code = generate_reset_code()

        store_reset_code(email, code)

        # Verify code is stored and can be retrieved
        assert verify_reset_code(email, code) is True
        assert verify_reset_code(email, 'wrongcode') is False

    def test_clear_reset_code(self):
        email = 'test@example.com'
        code = generate_reset_code()

        store_reset_code(email, code)
        assert verify_reset_code(email, code) is True

        clear_reset_code(email)
        assert verify_reset_code(email, code) is False

    def test_reset_code_expiration(self, settings):
        # Test with shorter timeout for faster testing
        settings.CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            }
        }

        email = 'test@example.com'
        code = generate_reset_code()

        # Store with 1 second timeout
        cache_key = f"password_reset_{email}"
        cache.set(cache_key, code, timeout=1)

        assert verify_reset_code(email, code) is True

        # Code should expire after 1 second
        import time
        time.sleep(1.1)
        assert verify_reset_code(email, code) is False
