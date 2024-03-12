"""
ASGI config for enchird_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os 
from django.core.asgi import get_asgi_application
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'enchird_backend.settings')
django.setup()

# from channels.http import AsgiHandler
from apis.messaging import routing
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from apis.messaging.middleware import TokenAuthMiddleware
# from .middleware import TokenAuthMiddlewareimport django



django_asgi_app = get_asgi_application()


application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": TokenAuthMiddleware(
            AuthMiddlewareStack(
                URLRouter(
                    routing.websocket_urlpatterns
                )
            )
    )
})


# application = ProtocolTypeRouter({
#     "http": django_asgi_app,
#     "websocket": MiddlewareStack([
#             TokenAuthMiddleware,
#             AuthMiddlewareStack(
#                 URLRouter(
#                     routing.websocket_urlpatterns
#                 )
#             )
#     ])
# })