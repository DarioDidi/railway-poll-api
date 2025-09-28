# polls/celery.py
import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poll_site.settings')

app = Celery('config')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Periodic tasks
app.conf.beat_schedule = {
    # 'send-poll-results-emails': {
    #    'task': 'polls.tasks.send_poll_results_emails',
    #    'schedule': 3600.0,  # Run every hour
    # },
    'check-database-connection': {
        'task': 'polls.tasks.check_database_connection',
        'schedule': 300.0,  # Run every 5 minutes
    },
    'check-api-health': {
        'task': 'polls.tasks.check_api_health',
        'schedule': 300.0,  # Run every 5 minutes
    },
    'cleanup-expired-polls': {
        'task': 'polls.tasks.cleanup_expired_polls',
        'schedule': 86400.0,  # Run daily
    },
}
