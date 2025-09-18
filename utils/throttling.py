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
        print("in get cache")
        print(f"getting cache key with views{view}")
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }

    # def parse_rate(self, rate):
    #    """
    #    Given the request rate string, return a two tuple of:
    #    <allowed number of requests>, <period of time in seconds>
    #    """
    #    if rate is None:
    #        return (None, None)
    #    num, period = rate.split('/')
    #    num_requests = int(num)
    #    duration = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}[period[0]]
    #    return (num_requests, duration)

    # def allow_request(self, request, view):
    #    print("cache befor:", self.cache.get('test_key', []))
    #    res = super().allow_request(request, view)
    #    print("RATE:", self.rate)
    #    print("KEY:", self.get_cache_key(request, view))
    #    print("KEY:", self.key)
    #    print("HISTORY:", self.history)
    #    print("cache:", self.cache.get(self.key, []))
    #    print("cache:", self.cache.get('test_key', []))
    #    print("reqs,duration",  self.num_requests, self.duration)
    #    print("before time", self.history[-1] <= self.now - self.duration)
    #    print("over:", len(self.history) >= self.num_requests)
    #    return res

    def allow_request(self, request, view):
        """
        Implement the check to see if the request should be throttled.

        On success calls `throttle_success`.
        On failure calls `throttle_failure`.
        """
        if self.rate is None:
            return True

        print("\ngetting key")
        self.key = self.get_cache_key(request, view)
        print("after key view:", view)
        if self.key is None:
            return True

        self.history = self.cache.get(self.key, [])
        self.now = self.timer()

        print("RATE:", self.rate)
        print("KEY:", self.get_cache_key(request, view))
        print("KEY:", self.key)
        print("HISTORY:", self.history)
        print("cache:", self.cache.get(self.key, []))
        print("cache:", self.cache.get('test_key', []))
        print("reqs,duration",  self.num_requests, self.duration)
        print("before time",
              self.history and self.history[-1] <= self.now - self.duration)
        print("over:", len(self.history) >= self.num_requests)
        # Drop any requests from the history which have now passed the
        # throttle duration
        while self.history and self.history[-1] <= self.now - self.duration:
            self.history.pop()
        if len(self.history) >= self.num_requests:
            return self.throttle_failure(request, view)
        return self.throttle_success()

    def throttle_failure(self, request, response):
        """
        Override to automatically block IPs that exceed the rate limit.
        """
        print(f"throttle failure request:{request}, response:{response}")
        # super().throttle_failure(request, response)
        super().throttle_failure()

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
                        " to excessive suspicious requests")
            )
            logger.warning(
                f"Automatically blocked suspicious IP: {ip_address}")
