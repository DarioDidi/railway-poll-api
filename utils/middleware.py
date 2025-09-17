# utils/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden
from polls.models import BlockedIP
import logging

logger = logging.getLogger(__name__)


class BlockedIPMiddleware(MiddlewareMixin):
    """
    Middleware to block requests from IP addresses in the blocked list.
    Logs suspicious activity for further analysis.
    """

    def process_request(self, request):
        ip_address = self.get_client_ip(request)

        if ip_address:
            # Check if IP is blocked
            if BlockedIP.objects.filter(
                ip_address=ip_address,
                is_active=True
            ).exists():
                logger.warning(
                    f"Blocked request from blocked IP: {ip_address}")
                return HttpResponseForbidden(
                    "Your IP address has been blocked"
                    "due to suspicious activity."
                )

        return None

    def get_client_ip(self, request):
        """
        Extract the client IP address from the request, handling proxies.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
