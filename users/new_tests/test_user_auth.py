# users/tests/test_auth_endpoints.py
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.core import mail
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
import pytest
from django.conf import settings

User = get_user_model()

USER_SETTINGS = getattr(settings, "REST_AUTH", None)


@pytest.mark.django_db
class TestAuthEndpoints:
    """Test cases for dj-rest-auth authentication endpoints"""

    def test_user_registration(self, client):
        """Test user registration endpoint"""
        url = reverse('rest_register')
        data = {
            'email': 'newuser@example.com',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
        }

        response = client.post(url, data, format='json')

        print(f"registration response:{response.data}")
        assert response.status_code == status.HTTP_201_CREATED
        # assert 'key' in response.data  # For token auth, or 'access' for JWT
        assert User.objects.filter(email='newuser@example.com').exists()

    def test_user_login(self, client, verified_user):
        """Test user login endpoint with verified user"""
        url = reverse('rest_login')
        data = {
            'email': 'verified@example.com',
            'password': 'testpass123'
        }

        response = client.post(url, data, format='json')
        print(f"user login response:{response.data}")
        assert response.status_code == status.HTTP_200_OK
        assert 'key' in response.data or 'access' in response.data

    def test_user_logout(self, authenticated_client):
        """Test user logout endpoint"""
        url = reverse('rest_logout')

        response = authenticated_client.post(url)

        print(f"logout response:{response.data}")
        assert response.status_code == status.HTTP_200_OK
        assert 'detail' in response.data

    def test_password_reset_request(self, client, user):
        """Test password reset request endpoint"""
        url = reverse('rest_password_reset')
        data = {'email': 'test@example.com'}

        with patch('allauth.account.adapter.DefaultAccountAdapter.send_mail')\
                as mock_send:
            mock_send.return_value = None
            response = client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'detail' in response.data

    def test_password_change(self, authenticated_client, user):
        """Test password change endpoint"""
        url = reverse('rest_password_change')
        data = {
            'old_password': 'testpass123',
            'new_password1': 'newcomplexpass123',
            'new_password2': 'newcomplexpass123'
        }

        # Debug: Check if user is authenticated
        print(f"User authenticated: {authenticated_client}")
        print(f"User in client: {getattr(authenticated_client, 'user', None)}")

        # Add headers to see what's being sent
        print(f"Request headers: {dict(authenticated_client._credentials)}")

        response = authenticated_client.post(url, data, format='json')
        print(f"Password change response status: {response.status_code}")
        print(f"Password change response data: {response.data}")

        # Check if session exists
        print(f"Session exists: {hasattr(authenticated_client, 'session')}")
        if hasattr(authenticated_client, 'session'):
            print(f"Session keys: {list(authenticated_client.session.keys())}")

        print(f"response data: {response.data}")
        assert response.status_code == status.HTTP_200_OK

    def test_user_detail_retrieve(self, authenticated_client, user):
        """Test retrieving user details"""
        url = reverse('rest_user_details')

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'verified@example.com'

    @patch('allauth.account.models.EmailAddress.send_confirmation')
    def test_email_verification_resend(self, mock_send_confirmation,
                                       authenticated_client, user):
        """Test resending email verification"""
        # url = reverse('rest_resend_email_verification')
        try:
            url = reverse('rest_resend_email')
        except Exception:
            try:
                url = reverse('resend-email-verification')
            except Exception:
                url = reverse('account_resend_email_verification')
        data = {'email': 'test@example.com'}

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        mock_send_confirmation.assert_called_once()

    def test_token_verify(self, authenticated_client):
        """Test token verification endpoint"""
        # First get a token

        login_url = reverse('rest_login')
        login_data = {
            'email': 'verified@example.com',
            'password': 'testpass123',
        }
        login_response = authenticated_client.post(
            login_url, login_data, format='json')
        print(f"getting token, login response:{login_response.data}")
        token = login_response.data.get(
            'key') or login_response.data.get('access')

        # Verify the token
        verify_url = reverse('rest_token_verify')
        # First get a token

        verify_data = {'token': token}

        response = authenticated_client.post(
            verify_url, verify_data, format='json')

        print(f"token verify response:{response.data}")
        assert response.status_code == status.HTTP_200_OK

    def test_token_refresh(self, authenticated_client):
        """Test token refresh endpoint handling both cookie and body tokens"""
        # First login
        login_url = reverse('rest_login')
        login_data = {
            'email': 'verified@example.com',
            'password': 'testpass123'
        }

        login_response = authenticated_client.post(
            login_url, login_data, format='json')

        # Try to get refresh token from response body first
        refresh_token = login_response.data.get('refresh')

        if refresh_token and refresh_token != '':
            # Refresh token in body - use it directly
            refresh_url = reverse('rest_token_refresh')
            refresh_data = {'refresh': refresh_token}
            response = authenticated_client.post(
                refresh_url, refresh_data, format='json')

            assert response.status_code == status.HTTP_200_OK
            assert 'access' in response.data

        elif hasattr(login_response, 'cookies') and 'polls-refresh-token'\
                in login_response.cookies:
            # Refresh token in cookie - make request without explicit token
            refresh_url = reverse('rest_token_refresh')
            response = authenticated_client.post(
                refresh_url, {}, format='json')

            assert response.status_code == status.HTTP_200_OK
            assert 'access' in response.data

        else:
            pytest.skip(
                "JWT refresh tokens not properly configured or available")

    def test_protected_endpoints_require_auth(self, client):
        """Test that protected endpoints require authentication"""
        client = APIClient()
        protected_endpoints = [
            # reverse('rest_logout'),
            reverse('rest_password_change'),
            reverse('rest_user_details'),
        ]

        for url in protected_endpoints:
            response = client.post(url)  # Try to access without auth
            print(f"response for url:{url}, data:{response.data}")
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    # def test_user_detail_update(self, authenticated_client, user):
    #    """Test updating user details"""
    #    url = reverse('rest_user_details')
    #    data = {
    #        'email': 'testupdate@example.com',
    #    }

    #    response = authenticated_client.patch(url, data, format='json')
    #    print(f"user detail update response data:{response.data}")

    #    assert response.status_code == status.HTTP_200_OK
    #    user.refresh_from_db()
    #    assert user.email == data['email']

    # def test_user_detail_update_debug(self, authenticated_client, user):
    #    """Debug the update process"""
    #    url = reverse('rest_user_details')

    #    # First, see what the current user data looks like
    #    get_response = authenticated_client.get(url)
    #    print("Current user data:", get_response.data)

    #    # Try to update email
    #    data = {'email': 'testupdate@example.com'}
    #    patch_response = authenticated_client.patch(url, data, format='json')

    #    print("Update response status:", patch_response.status_code)
    #    print("Update response data:", patch_response.data)

    #    # Check if email was actually updated
    #    user.refresh_from_db()
    #    print("User email after update:", user.email)

    #    # The test might be passing (200 OK) but email not actually changing
    #    assert patch_response.status_code == status.HTTP_200_OK
    # def test_debug_urls(self):
    #    """Debug all URL patterns"""
    #    from django.urls import get_resolver
    #    resolver = get_resolver()

    #    # Print all URL patterns
    #    print("Available URL patterns:")
    #    for pattern in resolver.url_patterns:
    #        print(f"  {pattern.pattern}")
    #        if hasattr(pattern, 'url_patterns'):
    #            for sub_pattern in pattern.url_patterns:
    #                print(f"    {sub_pattern.pattern} - {sub_pattern.name}")
