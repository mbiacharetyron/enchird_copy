"""
ASGI config for enchird_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os 
# from . import routing
from apis.messaging import routing
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from apis.messaging.middleware import TokenAuthMiddleware
# from .middleware import TokenAuthMiddleware


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'enchird_backend.settings')

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