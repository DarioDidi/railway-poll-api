# poll_site/urls.py(main urls)
from dj_rest_auth.jwt_auth import get_refresh_view
from rest_framework_simplejwt.views import TokenVerifyView
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from django.urls import path, include, re_path
from django.contrib import admin
# from dj_rest_auth.registration.views import RegisterView, VerifyEmailView
# from dj_rest_auth.views import (LoginView, LogoutView, UserDetailsView,
#                                PasswordResetView, PasswordResetConfirmView,
#                                PasswordChangeView)

schema_view = get_schema_view(
    openapi.Info(
        title="Polls API",
        default_version='v1',
        description="API for creating polls, voting, and fetching results",
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('admin/', admin.site.urls),

    # Dj-rest-auth endpoints
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('auth/', include('django.contrib.auth.urls')),

    path('api/auth/token/verify/', TokenVerifyView.as_view(),
         name='rest_token_verify'),
    path('api/auth/token/refresh/', get_refresh_view().as_view(),
         name='rest_token_refresh'),

    # polls
    path('api/', include('polls.urls')),

    # swagger docs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0),
            name='schema-json'),
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0),
         name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0),
         name='schema-redoc'),
]

# urlpatterns += [
#    re_path(r'token/verify/?$', TokenVerifyView.as_view(),
#            name='token_verify'),
# Explicit paths
# path('api/auth/login/', LoginView.as_view(), name='rest_login'),
# path('api/auth/logout/', LogoutView.as_view(), name='rest_logout'),
# path('api/auth/user/', UserDetailsView.as_view(),
#     name='rest_user_details'),
# path('api/auth/password/reset/', PasswordResetView.as_view(),
#     name='rest_password_reset'),
# path('api/auth/password/reset/confirm/',
#     PasswordResetConfirmView.as_view(),
#     name='rest_password_reset_confirm'),
# path('api/auth/password/change/', PasswordChangeView.as_view(),
#     name='rest_password_change'),

# path('api/auth/registration/', RegisterView.as_view(),
#     name='rest_register'),
# path('api/auth/registration/verify-email/',
#     VerifyEmailView.as_view(), name='rest_verify_email'),
#

# ]
