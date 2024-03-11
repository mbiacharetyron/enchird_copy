from django.urls import path
from .consumers import ChatConsumer, GroupChatConsumer

# ENDPOINT FOR FRONTEND TO USE

websocket_urlpatterns = [
    # path('ws/chat/<str:other_user>/?token=<str:token>/', ChatConsumer.as_asgi()),
    path('ws/chat/<str:other_user>/', ChatConsumer.as_asgi()),
    path('ws/group/<str:group_id>/<str:user_id>/', GroupChatConsumer.as_asgi()),
]