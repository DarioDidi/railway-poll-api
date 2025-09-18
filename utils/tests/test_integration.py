# utils/tests/test_integration.py
import pytest
from unittest.mock import Mock, patch
from django.test import RequestFactory, TestCase
from django.http import HttpResponse
from polls.models import BlockedIP
from utils.middleware import BlockedIPMiddleware
from utils.throttling import SuspiciousRequestThrottle


@pytest.mark.django_db
class TestTrafficControlIntegration(TestCase):
    """Integration tests for the complete traffic control system"""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = BlockedIPMiddleware(
            get_response=lambda request: HttpResponse())
        self.throttle = SuspiciousRequestThrottle()

    def test_complete_blocking_flow(self):
        """Test the complete flow from throttling to blocking"""
        # Create a request that will be throttled
        request = self.factory.get('/api/auth/login/')
        request.META['REMOTE_ADDR'] = '192.168.1.100'
        request.user = Mock()
        request.user.is_authenticated = False

        # Simulate throttle failure (too many requests)
        response = Mock()
        response.status_code = 429

        # Mock the cache operations
        with patch.object(self.throttle, 'wait'):
            with patch.object(self.throttle, 'cache') as mock_cache:
                mock_cache.get.return_value = [
                    'req1', 'req2', 'req3', 'req4', 'req5']

                # This should trigger IP blocking
                self.throttle.throttle_failure(request, response)

        # Verify the IP was blocked
        blocked_ip = BlockedIP.objects.get(ip_address='192.168.1.100')
        assert blocked_ip.is_active is True
        assert 'excessive suspicious requests' in blocked_ip.reason

        # Now test that the middleware blocks this IP
        blocked_request = self.factory.get('/api/polls/')
        blocked_request.META['REMOTE_ADDR'] = '192.168.1.100'

        middleware_response = self.middleware.process_request(blocked_request)
        self.assertIsNotNone(middleware_response)
        self.assertEqual(middleware_response.status_code, 403)

    @patch('utils.throttling.logger')
    @patch('utils.middleware.logger')
    def test_suspicious_activity_logging(self, mock_middleware_logger, mock_throttling_logger):
        """Test that suspicious activity is logged throughout the system"""
        # Create a suspicious request
        request = self.factory.post('/api/auth/login/')
        request.META['REMOTE_ADDR'] = '192.168.1.100'
        request.user = Mock()
        request.user.is_authenticated = False

        # Test middleware logging
        middleware = BlockedIPMiddleware(
            get_response=lambda request: HttpResponse(status=400))
        response = HttpResponse(status=400)

        middleware.process_response(request, response)

        # Middleware should log the suspicious request
        mock_middleware_logger.warning.assert_called()

        # Test throttle logging
        throttle_response = Mock()
        throttle_response.status_code = 429

        with patch.object(self.throttle, 'wait'):
            self.throttle.throttle_failure(request, throttle_response)

        # Throttle should log the blocking action
        mock_throttling_logger.warning.assert_called()
