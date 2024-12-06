# app/routing.py
from django.urls import re_path
from .consumers import ChatConsumer  # Đảm bảo rằng đường dẫn này đúng

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', ChatConsumer.as_asgi()),
]