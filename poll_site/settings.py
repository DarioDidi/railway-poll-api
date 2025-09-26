import os
# import dj_database_url

from pathlib import Path
from django.utils.timezone import timedelta
from dotenv import load_dotenv
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

API_BASE_URL = os.environ.get('API_BASE_URL', default='http://localhost:8000')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/


SECRET_KEY = os.environ.get("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!

# DEBUG = True
DEBUG = False

ALLOWED_HOSTS = ['localhost']

AUTH_USER_MODEL = "users.User"

# Application definition

INSTALLED_APPS = [
    'daphne',
    'channels',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # allauth
    # 'django.contrib.sites',
    # 'allauth',
    # 'allauth.account',
    # 'allauth.socialaccount',

    # rest auth
    'rest_framework_simplejwt',
    # 'dj_rest_auth',
    # 'dj_rest_auth.registration',

    'rest_framework',
    'rest_framework.authtoken',
    'drf_yasg',
    'corsheaders',
    'django_filters',

    # custom apps
    'users',
    'polls',
]

MIDDLEWARE = [

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Custom middleware for IP blocking and monitoring
    'utils.middleware.BlockedIPMiddleware',
    'utils.middleware.SuspiciousRequestMiddleware',

    # allauth middleware
    # 'allauth.account.middleware.AccountMiddleware',
    # serve these static assets from Render's web server.
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'poll_site.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # 'DIRS': [],
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                # `allauth` needs this from django
                # 'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'poll_site.wsgi.application'

# Channel layers (using Redis as backend)
ASGI_APPLICATION = 'poll_site.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],  # Adjust for your Redis server
        },
    },
}

if not DEBUG:
    CHANNEL_LAYERS['default']['CONFIG']['hosts'] = [
        (os.environ.get('REDIS_URL', 'redis://localhost:6379'))
    ]

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# DATABASES = {
#    'default': dj_database_url.config(
#        # Replace this value with your local database's connection string.
#        default='postgresql://postgres:postgres@localhost:5432/mysite',
#        conn_max_age=600
#    )
# }


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': ('django.contrib.auth.password_validation'
                 '.UserAttributeSimilarityValidator'),
    },
    {
        'NAME': ('django.contrib.auth.password_validation.'
                 'MinimumLengthValidator'),
    },
    {
        'NAME': ('django.contrib.auth.password_validation.'
                 'CommonPasswordValidator'),
    },
    {
        'NAME': ('django.contrib.auth.password_validation.'
                 'NumericPasswordValidator'),
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

# STATIC_URL = 'static/'
STATIC_URL = '/static/'

# This production code might break development mode,
# so we check whether we're in DEBUG mode
if not DEBUG:
    # Tell Django to copy static assets into a path called `staticfiles`
    # (this is specific to Render)
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

    # Enable the WhiteNoise storage backend,
    # which compresses static files to reduce disk use
    # and renames the files with unique names
    # for each version to support long-term caching
    STATICFILES_STORAGE = \
        'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Required for allauth
# SITE_ID = 1


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        # 'dj_rest_auth.jwt_auth.JWTCookieAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        # 'rest_framework.authentication.TokenAuthentication',
        # 'rest_framework.authentication.SessionAuthentication',
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
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
        'suspicious': '5/minute',
        # 'suspicious': '5/m',
    },
    'DEFAULT_PAGINATION_CLASS': ('rest_framework.'
                                 'pagination.PageNumberPagination'),
    'PAGE_SIZE': 20,
}

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',
    # `allauth` specific authentication methods, such as login by email
    # 'allauth.account.auth_backends.AuthenticationBackend',
]

# JWT settings
REST_USE_JWT = True
JWT_AUTH_COOKIE = 'polls-auth'
# JWT_AUTH_REFRESH_COOKIE = 'polls-refresh-token'

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
}

# Django Allauth Settings
# ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
# ACCOUNT_USER_MODEL_USERNAME_FIELD = None
# ACCOUNT_LOGIN_METHODS = ["email"]
# ACCOUNT_USERNAME_REQUIRED = False
#
#
# ACCOUNT_SIGNUP_FIELDS = ['email*',  'password1*', 'password2*']
#
# To avoid Rendering email confirmation template
# ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = '/api/auth/verified/'
# ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = '/api/auth/verified/'
#
# Disable allauth templates
# This will automatically confirm email on link click
# ACCOUNT_CONFIRM_EMAIL_ON_GET set to True
# the user will confirm the e-mail just by clicking the link
# ACCOUNT_CONFIRM_EMAIL_ON_GET = True
# CONFIRM_EMAIL_ON_GET = True

# Email backend for development
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_TIMEOUT = 30
# Email configuration
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

# Dj-rest-auth settings
# REST_AUTH = {
#    'USE_JWT': True,
#    # Make sure this is False to get refresh token in response
#    # WARNING: CHANGE IN PRODUCTION!!!!
#
#    # 'JWT_AUTH_HTTPONLY': False,
#    'JWT_AUTH_COOKIE': 'polls-auth',
#    'JWT_AUTH_REFRESH_COOKIE': 'polls-refresh-token',
#    'JWT_AUTH_REFRESH_COOKIE_PATH': '/',
#    'JWT_AUTH_SAMESITE': 'Lax',
#    'REGISTER_SERIALIZER': 'users.serializers.CustomRegisterSerializer',
#
#    # Disable template rendering for email verification
#    'EMAIL_VERIFICATION_SENT_WHEN_REGISTERING': False,
# }

# To completely suppress the warnings
# warnings.filterwarnings("ignore",
#                        message="app_settings.USERNAME_REQUIRED is deprecated")
# warnings.filterwarnings("ignore",
#                        message="app_settings.EMAIL_REQUIRED is deprecated")

SWAGGER_SETTINGS = {
    "DEFAULT_INFO": 'poll_site.urls.api_info'
}
SWAGGER_USE_COMPAT_RENDERERS = False


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
}

# Celery configuration
CELERY_BROKER_URL = os.environ.get(
    'CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get(
    'CELERY_BROKER_URL', 'redis://localhost:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
