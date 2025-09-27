# poll_site/urls.py(main urls)
from rest_framework import permissions

from django.urls import path, include, re_path
from django.contrib import admin

from polls.views import health_check, root_view


from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from drf_yasg.generators import OpenAPISchemaGenerator
# Swagger open ai info
api_info = openapi.Info(
    title="Polls API",
    default_version='v1',
    description="API for creating polls, voting, and fetching results",
    license=openapi.License(name="BSD License"),
)


class BothHttpAndHttpsSchemaGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        schema.schemes = ["http", "https"]
        return schema


schema_view = get_schema_view(
    public=True,
    permission_classes=(permissions.AllowAny,),
    generator_class=BothHttpAndHttpsSchemaGenerator,
)

urlpatterns = [
    # root
    path('', root_view),

    # admin
    path('admin/', admin.site.urls),

    # health check for render
    path('api/health/', health_check),

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
