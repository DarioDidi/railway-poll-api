# users/utils.py
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import jwt
from datetime import datetime, timedelta


def generate_email_verification_token(user):
    """
    Generate a JWT token for email verification.
    """
    payload = {
        'user_id': str(user.id),
        'email': user.email,
        'purpose': 'email_verification',
        # expires in 24hrs
        'exp': datetime.utcnow() + timedelta(hours=24)
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')


def generate_password_reset_token(user):
    """
    Generate a JWT token for password reset.
    """
    payload = {
        'user_id': str(user.id),
        'email': user.email,
        'purpose': 'password_reset',
        # Token expires in 1 hour
        'exp': datetime.utcnow() + timedelta(hours=1)
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')


def verify_token(token, purpose):
    """
    Verify JWT token and return user if valid.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])

        # Check if token purpose matches
        if payload.get('purpose') != purpose:
            return None

        # Check if token is expired
        if datetime.utcfromtimestamp(payload['exp']) < datetime.utcnow():
            return None

        # Get user from payload
        from .models import User
        try:
            user = User.objects.get(
                id=payload['user_id'], email=payload['email'])
            return user
        except User.DoesNotExist:
            return None

    except (jwt.InvalidTokenError, KeyError):
        return None


def send_verification_email(user, request):
    """
    Send email verification message to user.
    """
    token = generate_email_verification_token(user)
    verification_url = \
        f"{settings.FRONTEND_URL}/auth/verify-email?token={token}"

    subject = "Verify Your Email Address"
    html_message = render_to_string('emails/verify_email.html', {
        'user': user,
        'verification_url': verification_url,
        'expiry_hours': 24
    })
    plain_message = strip_tags(html_message)

    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_password_reset_email(user, request):
    """
    Send password reset email to user.
    """
    token = generate_password_reset_token(user)
    reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={token}"

    subject = "Reset Your Password"
    html_message = render_to_string('emails/reset_password.html', {
        'user': user,
        'reset_url': reset_url,
        'expiry_hours': 1
    })
    plain_message = strip_tags(html_message)

    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )
