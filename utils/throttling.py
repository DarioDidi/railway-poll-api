# utils/throttling.py
from rest_framework.throttling import SimpleRateThrottle
from polls.models import BlockedIP
import logging

logger = logging.getLogger(__name__)


class SuspiciousRequestThrottle(SimpleRateThrottle):
    """
    Custom throttle to detect and handle suspicious request patterns.
    Automatically blocks IPs that exceed the suspicious rate limit.
    """
    scope = 'suspicious'

    def get_cache_key(self, request, view):
        # Use IP address for anonymous users, user ID for authenticated users
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }

    def throttle_failure(self, request, response):
        """
        Override to automatically block IPs that exceed the rate limit.
        """
        super().throttle_failure(request, response)

        # Block the IP if it's making suspicious requests
        ip_address = self.get_ident(request)
        if ip_address and not request.user.is_authenticated:
            self.block_suspicious_ip(ip_address)

        return response

    def block_suspicious_ip(self, ip_address):
        """
        Automatically block an IP address due to suspicious activity.
        """
        if not BlockedIP.objects.filter(ip_address=ip_address).exists():
            BlockedIP.objects.create(
                ip_address=ip_address,
                reason=("Automatically blocked due"
                        "to excessive suspicious requests")
            )
            logger.warning(
                f"Automatically blocked suspicious IP: {ip_address}")
