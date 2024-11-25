from django.urls import path
from . import consumers
from django.urls import path
from .views import RoomListView, MessageListView, test_view

websocket_urlpatterns = [
    path('ws/chat/<str:room_name>/', consumers.ChatConsumer.as_asgi()),
]

urlpatterns = [
    path('rooms/', RoomListView.as_view(), name='room-list'),
    path('rooms/<str:room_name>/messages/', MessageListView.as_view(), name='message-list'),
    path('test/', test_view, name='test'),
]
