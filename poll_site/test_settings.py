from poll_site.settings import *

SECURE_SSL_REDIRECT = False

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'utils.throttling.SuspiciousRequestThrottle',
    ],
    'DEFAULT_PAGINATION_CLASS': ('rest_framework.'
                                 'pagination.PageNumberPagination'),
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
        'suspicious': '5/minute',
        # 'suspicious': '5/m',
    },
}

SECURE_PROXY_SSL_HEADER = ()
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = False
CSRF_TRUSTED_ORIGINS = [
    '*'
]
