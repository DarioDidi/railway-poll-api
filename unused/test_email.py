from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Test email configuration'

    def handle(self, *args, **options):
        try:
            send_mail(
                'Test Email',
                'This is a test email from your Django app.',
                settings.DEFAULT_FROM_EMAIL,
                ['co3ddder@gmail.com'],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS('Email sent successfully!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error sending email: {e}'))
