# utils/tests/test_throttling.py

from django.utils import timezone
import pytest
from unittest.mock import Mock, patch
from django.core.cache import cache
from django.test import RequestFactory
from polls.models import BlockedIP
from utils.throttling import SuspiciousRequestThrottle


@pytest.mark.django_db
class TestSuspiciousRequestThrottle:
    """Test the suspicious request throttling functionality"""

    def setup_method(self):
        """Clear cache before each test"""
        cache.clear()

    def test_get_cache_key_anonymous_user(self):
        """Test cache key generation for anonymous users"""
        throttle = SuspiciousRequestThrottle()
        factory = RequestFactory()

        request = factory.get('/api/auth/login/')
        request.META['REMOTE_ADDR'] = '192.168.1.100'
        request.user = Mock()  # Mock anonymous user
        request.user.is_authenticated = False

        cache_key = throttle.get_cache_key(request, None)
        assert 'suspicious' in cache_key
        assert '192.168.1.100' in cache_key

    def test_get_cache_key_authenticated_user(self):
        """Test cache key generation for authenticated users"""
        throttle = SuspiciousRequestThrottle()
        factory = RequestFactory()

        request = factory.get('/api/auth/login/')
        request.user = Mock()
        request.user.is_authenticated = True
        request.user.pk = 123

        cache_key = throttle.get_cache_key(request, None)
        assert 'suspicious' in cache_key
        assert '123' in cache_key  # Should use user ID

    @patch('utils.throttling.BlockedIP.objects')
    def test_throttle_failure_blocks_ip(self, mock_blocked_ip_manager):
        """Test that throttle failure blocks IP addresses"""
        mock_blocked_ip_manager.filter.return_value.exists.return_value = False
        mock_blocked_ip_manager.create.return_value = None

        throttle = SuspiciousRequestThrottle()
        factory = RequestFactory()

        request = factory.get('/api/auth/login/')
        request.META['REMOTE_ADDR'] = '192.168.1.100'
        request.user = Mock()
        request.user.is_authenticated = False

        response = Mock()
        response.status_code = 429

        # Mock the parent method to avoid actual cache operations
        # with patch.object(throttle, 'wait') as mock_wait:
        with patch.object(throttle, 'wait') as _:
            throttle.throttle_failure(request, response)

        # Should attempt to create a blocked IP entry
        mock_blocked_ip_manager.create.assert_called_once_with(
            ip_address='192.168.1.100',
            reason="Automatically blocked due to excessive suspicious requests"
        )

    @patch('utils.throttling.BlockedIP.objects')
    def test_throttle_failure_existing_block(self, mock_blocked_ip_manager):
        """Test that throttle failure doesn't duplicate existing blocks"""
        mock_blocked_ip_manager.filter.return_value.exists.return_value = True

        throttle = SuspiciousRequestThrottle()
        factory = RequestFactory()

        request = factory.get('/api/auth/login/')
        request.META['REMOTE_ADDR'] = '192.168.1.100'
        request.user = Mock()
        request.user.is_authenticated = False

        response = Mock()
        response.status_code = 429

        with patch.object(throttle, 'wait') as _:
            throttle.throttle_failure(request, response)

        # Should not create duplicate block
        mock_blocked_ip_manager.create.assert_not_called()

    @patch('utils.throttling.logger')
    def test_block_suspicious_ip_logging(self, mock_logger):
        """Test that IP blocking is logged"""
        throttle = SuspiciousRequestThrottle()

        # Mock the database operations
        with patch.object(BlockedIP.objects, 'filter') as mock_filter, \
                patch.object(BlockedIP.objects, 'create') as mock_create:

            mock_filter.return_value.exists.return_value = False
            mock_create.return_value = None

            throttle.block_suspicious_ip('192.168.1.100')

            # Should log the blocking action
            mock_logger.warning.assert_called_once()
            args, _ = mock_logger.warning.call_args
            log_message = args[0]
            assert '192.168.1.100' in log_message

    def test_throttle_rate_limiting(self):
        """Test that the throttle actually limits requests"""
        throttle = SuspiciousRequestThrottle()
        factory = RequestFactory()

        # First request should be allowed
        request = factory.get('/api/auth/login/')
        request.META['REMOTE_ADDR'] = '192.168.1.100'
        request.user = Mock()
        request.user.is_authenticated = False

        # Mock the rate check
        with patch.object(throttle, 'get_cache_key') as mock_key, \
                patch.object(throttle, 'cache') as mock_cache:

            mock_key.return_value = 'test_key'
            # No previous requests
            mock_cache.get.return_value = []

            # First request should be allowed
            first_result = throttle.allow_request(request, None)
            print("first req result:", first_result)
            assert first_result is True

            # Simulate 5 previous requests in the last minute
            mock_cache.get.return_value = [
                timezone.now().timestamp() for _ in range(5)]
            print("in test mocked ret value:", mock_cache.get(mock_key))

            # Sixth request should be throttled
            assert throttle.allow_request(request, None) is False
