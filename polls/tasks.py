# polls/tasks.py
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db import connection
import requests
from .models import Poll


@shared_task
def send_poll_results_email(poll_id, recipient_emails):
    """
    Send poll results via email to participants after a poll closes.
    """
    try:
        poll = Poll.objects.get(id=poll_id)
        results = poll.get_results()

        subject = f"Results for your poll: {poll.question[:50]}..."

        message = f"""
        Poll: {poll.question}\n
        Results:
        """

        for result in results:
            message += f"\n- {result['option']}: {result['votes']}"
            message += f" votes ({result['percentage']:.2f}%)"

        message += f"\n\nTotal votes: {sum(result['votes'] for result in results)}"
        message += f"\nPoll closed on: {poll.expiry_date}"

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_emails,
            fail_silently=False,
        )

        return f"Results email sent for poll {poll_id} to {len(recipient_emails)} recipients"

    except Poll.DoesNotExist:
        return f"Poll {poll_id} not found"


@shared_task
def send_poll_results_emails():
    """
    Task to send result emails for all polls that ended in the last hour.
    """
    one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
    recently_ended_polls = Poll.objects.filter(
        expiry_date__lte=timezone.now(),
        expiry_date__gte=one_hour_ago,
        is_active=True
    )

    for poll in recently_ended_polls:
        # Get all participant emails
        participant_emails = set()
        for vote in poll.votes.all():
            if vote.user and vote.user.email:
                participant_emails.add(vote.user.email)

        if participant_emails:
            send_poll_results_email.delay(
                str(poll.id),
                list(participant_emails)
            )

    return f"Processed {recently_ended_polls.count()} recently ended polls"


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
