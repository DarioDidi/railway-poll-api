# utils/tests/test_middleware.py
import pytest
from django.test import RequestFactory
from django.http import HttpResponse
from utils.middleware import BlockedIPMiddleware


@pytest.mark.django_db
class TestBlockedIPMiddleware:
    """Test IP blocking middleware functionality"""

    def test_blocked_ip_middleware(self, blocked_ip):
        """Test that blocked IPs are rejected"""
        middleware = BlockedIPMiddleware(
            get_response=lambda request: HttpResponse())
        factory = RequestFactory()

        # Create request from blocked IP
        request = factory.get('/api/polls/')
        request.META['REMOTE_ADDR'] = '192.168.1.100'

        response = middleware.process_request(request)
        assert response.status_code == 403
        assert "blocked" in response.content.decode().lower()

    def test_allowed_ip_middleware(self):
        """Test that allowed IPs can pass through"""
        middleware = BlockedIPMiddleware(
            get_response=lambda request: HttpResponse())
        factory = RequestFactory()

        # Create request from allowed IP
        request = factory.get('/api/polls/')
        request.META['REMOTE_ADDR'] = '192.168.1.200'

        response = middleware.process_request(request)
        assert response is None  # Should return None to continue processing
