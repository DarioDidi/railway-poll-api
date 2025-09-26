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

    def allow_request(self, request, view):
        """
        Implement the check to see if the request should be throttled.

        On success calls `throttle_success`.
        On failure calls `throttle_failure`.
        """
        ip_address = self.get_ident(request)
        # skip local
        if ip_address == '127.0.0.1' or ip_address == "0.0.0.0":
            return True
        self.rate = self.get_rate()
        self.num_requests, self.duration = self.parse_rate(self.rate)
        if self.rate is None:
            return True

        self.key = self.get_cache_key(request, view)
        if self.key is None:
            return True

        print("\n\n\n\nTHROTTLING:\n\n\n")
        self.history = self.cache.get(self.key, [])
        self.now = self.timer()

        # Drop any requests from the history which have now passed the
        # throttle duration
        while self.history and self.history[-1] <= self.now - self.duration:
            self.history.pop()
        if len(self.history) >= self.num_requests:
            # pass correct argument required by override
            return self.throttle_failure(request, view)
        print("going to throttle success")
        return self.throttle_success()

    def throttle_failure(self, request, response):
        """
        Override to automatically block IPs that exceed the rate limit.
        """
        res = super().throttle_failure()

        # Block the IP if it's making suspicious requests
        ip_address = self.get_ident(request)
        if (ip_address and
                not request.user.is_authenticated):
            self.block_suspicious_ip(ip_address)

        return res

    def block_suspicious_ip(self, ip_address):
        """
        Automatically block an IP address due to suspicious activity.
        """
        if not BlockedIP.objects.filter(ip_address=ip_address).exists():
            BlockedIP.objects.create(
                ip_address=ip_address,
                reason=("Automatically blocked due"
                        " to excessive suspicious requests")
            )
            logger.warning(
                f"Automatically blocked suspicious IP: {ip_address}")
