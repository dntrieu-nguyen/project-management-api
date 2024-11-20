from django.urls import path
from . import consumers
from django.urls import path
from .views import RoomListView, MessageListView
from drf_yasg import openapi
from rest_framework import permissions

websocket_urlpatterns = [
    path('ws/chat/<str:room_name>/', consumers.ChatConsumer.as_asgi()),
]

urlpatterns = [
    path('rooms/', RoomListView.as_view(), name='room-list'),
    path('rooms/<str:room_name>/messages/', MessageListView.as_view(), name='message-list'),
]
