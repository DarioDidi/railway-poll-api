# polls/tasks.py
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from django.db import connection
import requests
from .models import Poll


@shared_task
def check_database_connection():
    """
    Periodic task to verify database connection is working.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return "Database connection OK"
    except Exception as e:
        # Log error and potentially trigger alert
        return f"Database connection failed: {str(e)}"


@shared_task
def check_api_health():
    """
    Periodic task to check if API health endpoint returns 200.
    """
    try:
        # This would need to be your actual API URL
        response = requests.get(
            f"{settings.BASE_URL}/api/docs/",
            timeout=10
        )
        if response.status_code == 200:
            return "API health check OK"
        else:
            return f"API health check failed status {response.status_code}"
    except Exception as e:
        return f"API health check failed: {str(e)}"


@shared_task
def cleanup_expired_polls():
    """
    Clean up old polls and related data to maintain database performance.
    """
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    old_polls = Poll.objects.filter(expiry_date__lt=thirty_days_ago)

    count = old_polls.count()
    old_polls.delete()

    return f"Cleaned up {count} expired polls"
