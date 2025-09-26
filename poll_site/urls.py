# poll_site/urls.py(main urls)
# from dj_rest_auth.jwt_auth import get_refresh_view
# from rest_framework_simplejwt.views import TokenVerifyView
from rest_framework import permissions

from django.urls import path, include, re_path
from django.contrib import admin

# from users.views import APIConfirmEmailView
# from users.views import SimpleConfirmEmailView

from drf_yasg import openapi
from drf_yasg.views import get_schema_view
# Swagger open ai info
api_info = openapi.Info(
    title="Polls API",
    default_version='v1',
    description="API for creating polls, voting, and fetching results",
    license=openapi.License(name="BSD License"),
)
schema_view = get_schema_view(
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('admin/', admin.site.urls),

    # Override the default email confirmation URL
    # path('api/auth/registration/account-confirm-email/<str:key>/',
    #     APIConfirmEmailView.as_view(),
    #     name='account_confirm_email'),
    # override token views
    # path('api/auth/token/verify/', TokenVerifyView.as_view(),
    #     name='rest_token_verify'),
    # path('api/auth/token/refresh/', get_refresh_view().as_view(),
    #     name='rest_token_refresh'),

    # Dj-rest-auth endpoints
    # path('api/auth/', include('dj_rest_auth.urls')),

    # path('api/auth/registration/',
    # include('dj_rest_auth.registration.urls')),
    # path('auth/', include('django.contrib.auth.urls')),

    # custom auth
    path('api/', include('users.urls')),
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
