from django.core.management.base import BaseCommand
from polls.models import BlockedIP


class Command(BaseCommand):
    help = 'Block an IP address'

    def add_arguments(self, parser):
        parser.add_argument('ip_address', type=str,
                            help='IP to block')

    def handle(self, *args, **kwargs):
        # ip_addr = args[0]
        ip_address = kwargs['ip_address']

        # Check if already blocked
        if BlockedIP.objects.filter(ip_address=ip_address).exists():
            self.stdout.write(
                self.style.WARNING(f'IP {ip_address} is already blocked')
            )
            return
        if not self.is_valid_ip(ip_address):
            self.stdout.write(self.style.WARNING(
                f"Invalid IP address: {ip_address}"))
            return

        # Create or update blocked IP entry
        obj, created = BlockedIP.objects.update_or_create(
            ip_address=ip_address,
        )
        self.stdout.write(
            self.style.SUCCESS(f'Successfully blocked IP: {ip_address}')
        )

    def is_valid_ip(self, ip_address):
        """
        Basic validation for IP address format.
        """
        import re
        ipv4_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^::1$|^::$'

        return re.match(ipv4_pattern, ip_address) or re.match(ipv6_pattern, ip_address)
