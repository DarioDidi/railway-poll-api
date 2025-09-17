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

        # Block the IP
        BlockedIP.objects.create(ip_address=ip_address)
        self.stdout.write(
            self.style.SUCCESS(f'Successfully blocked IP: {ip_address}')
        )
