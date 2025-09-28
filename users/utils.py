# users/utils.py
# from django.core.mail import send_mail
# from django.template.loader import render_to_string
# from django.utils.html import strip_tags
from django.conf import settings
from .models import User, PasswordResetToken
import jwt
import secrets
from datetime import datetime, timedelta
# from django.utils import timezone
from django.core.cache import cache


# def generate_jwt_token(user, purpose, expiry_hours=24):
#    """Generate a JWT token for various purposes"""
#    payload = {
#        'user_id': str(user.id),
#        'email': user.email,
#        'purpose': purpose,
#        'exp': datetime.utcnow() + timedelta(hours=expiry_hours)
#    }
#    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
#
#
# def verify_jwt_token(token, purpose):
#    """Verify JWT token and return user if valid"""
#    try:
#        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
#
#        if payload.get('purpose') != purpose:
#            return None
#
#        if datetime.utcfromtimestamp(payload['exp']) < datetime.utcnow():
#            return None
#
#        try:
#            user = User.objects.get(
#                id=payload['user_id'], email=payload['email'])
#            return user
#        except User.DoesNotExist:
#            return None
#
#    except (jwt.InvalidTokenError, KeyError):
#        return None
#
#
# def generate_unique_token():
#    """Generate a unique token for database storage"""
#    return secrets.token_urlsafe(32)


# def create_email_verification_token(user):
#    """Create and store email verification token"""
#    # Invalidate existing tokens
#    EmailVerificationToken.objects.filter(
#        user=user, used=False).update(used=True)
#
#    token = generate_unique_token()
#    EmailVerificationToken.objects.create(
#        user=user,
#        token=token
#    )
#    return token


# def create_password_reset_token(user):
#    """Create and store password reset token"""
#    # Invalidate existing tokens
#    PasswordResetToken.objects.filter(user=user, used=False).update(used=True)
#
#    token = generate_unique_token()
#    PasswordResetToken.objects.create(
#        user=user,
#        token=token
#    )
#    return token
#

# def verify_email_token(token):
#    """Verify email verification token from database"""
#    try:
#        verification_token = EmailVerificationToken.objects.get(
#            token=token,
#            used=False
#        )
#
#        if verification_token.is_expired():
#            return None
#
#        return verification_token.user
#    except EmailVerificationToken.DoesNotExist:
#        return None


def verify_password_reset_token(token):
    """Verify password reset token from database"""
    try:
        reset_token = PasswordResetToken.objects.get(
            token=token,
            used=False
        )

        if reset_token.is_expired():
            return None

        return reset_token.user
    except PasswordResetToken.DoesNotExist:
        return None


def generate_reset_code():
    """Generate a simple 6-digit reset code"""
    return ''.join(secrets.choice('0123456789') for _ in range(6))


def store_reset_code(email, code):
    """Store reset code in cache for 15 minutes"""
    cache_key = f"password_reset_{email}"
    cache.set(cache_key, code, timeout=900)  # 15 minutes
    return code


def verify_reset_code(email, code):
    """Verify reset code from cache"""
    cache_key = f"password_reset_{email}"
    stored_code = cache.get(cache_key)
    return stored_code == code


def clear_reset_code(email):
    """Clear used reset code"""
    cache_key = f"password_reset_{email}"
    cache.delete(cache_key)
# def send_verification_email(user, request=None):
#    """Send email verification message"""
#    token = create_email_verification_token(user)
#
#    # Use API endpoint for verification instead of frontend URL
#    verification_url = (
#        f"{settings.API_BASE_URL}/api/auth/registration/verify-email/{token}/")
#
#    subject = "Verify Your Email Address"
#    html_message = render_to_string('emails/verify_email.html', {
#        'user': user,
#        'verification_url': verification_url,
#        'expiry_hours': 24
#    })
#    plain_message = strip_tags(html_message)
#
#    send_mail(
#        subject,
#        plain_message,
#        settings.DEFAULT_FROM_EMAIL,
#        [user.email],
#        html_message=html_message,
#        fail_silently=False,
#    )
#
#    # Update last email sent time
#    user.last_email_sent = timezone.now()
#    user.save(update_fields=['last_email_sent'])


# def send_password_reset_email(user, request=None):
#    """Send password reset email"""
#    token = create_password_reset_token(user)
#
#    # Provide token for frontend to use with API
#    reset_url = f"{settings.API_BASE_URL}/api/auth/password/reset/confirm/"
#
#    subject = "Reset Your Password"
#    html_message = render_to_string('emails/reset_password.html', {
#        'user': user,
#        'reset_token': token,
#        'api_endpoint': reset_url,
#        'expiry_hours': 1
#    })
#    plain_message = strip_tags(html_message)
#
#    send_mail(
#        subject,
#        plain_message,
#        settings.DEFAULT_FROM_EMAIL,
#        [user.email],
#        html_message=html_message,
#        fail_silently=False,
#    )
