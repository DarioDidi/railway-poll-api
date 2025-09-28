# utils/tests/test_middleware.py
import pytest
from django.test import RequestFactory
from django.http import HttpResponse
from utils.middleware import BlockedIPMiddleware

from polls.models import BlockedIP


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
        assert response is None

    def test_blocked_ip_middleware_inactive_block(self):
        """Test that inactive blocks don't affect requests"""
        # Create an inactive block
        BlockedIP.objects.create(
            ip_address='192.168.1.100',
            reason='Inactive test',
            is_active=False
        )

        middleware = BlockedIPMiddleware(
            get_response=lambda request: HttpResponse())
        factory = RequestFactory()

        # Create request from "blocked" but inactive IP
        request = factory.get('/api/polls/')
        request.META['REMOTE_ADDR'] = '192.168.1.100'

        response = middleware.process_request(request)
        # Should allow through since block is inactive
        assert response is None

    def test_get_client_ip_with_x_forwarded_for(self):
        """Test IP extraction with X-Forwarded-For header"""
        middleware = BlockedIPMiddleware(
            get_response=lambda request: HttpResponse())
        factory = RequestFactory()

        # Test with X-Forwarded-For header
        request = factory.get('/api/polls/')
        request.META['HTTP_X_FORWARDED_FOR'] = '192.168.1.50, 10.0.0.1'
        request.META['REMOTE_ADDR'] = '10.0.0.1'

        ip = middleware.get_client_ip(request)
        assert ip == '192.168.1.50'  # Should use first IP from X-Forwarded-For

    def test_get_client_ip_without_x_forwarded_for(self):
        """Test IP extraction without X-Forwarded-For header"""
        middleware = BlockedIPMiddleware(
            get_response=lambda request: HttpResponse())
        factory = RequestFactory()

        # Test without X-Forwarded-For header
        request = factory.get('/api/polls/')
        request.META['REMOTE_ADDR'] = '192.168.1.100'

        ip = middleware.get_client_ip(request)
        assert ip == '192.168.1.100'  # Should use
