import os
from django.core.asgi import get_asgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poll_site.settings')
#IMPORTANT: get ASGI before any other imports
application = get_asgi_application()

import polls.routing

from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from channels.routing import ProtocolTypeRouter, URLRouter



application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                polls.routing.websocket_urlpatterns
                # websocket_urlpatterns
            )
        )
    ),
})
