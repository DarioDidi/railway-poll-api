# users/utils.py
import secrets
from django.core.cache import cache


def generate_reset_code():
    """Generate a simple 6-digit reset code"""
    return ''.join(secrets.choice('0123456789') for _ in range(6))


def store_reset_code(email, code):
    """Store reset code in cache for 15 minutes"""
    cache_key = f"password_reset_{email}"
    cache.set(cache_key, code, timeout=900)
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
