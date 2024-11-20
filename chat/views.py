from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from app.models import Room, Message
from utils.response import failure_response, success_response
from .serializers import RoomSerializer, MessageSerializer

class RoomListView(APIView):
    """
    API để lấy danh sách phòng chat.
    """
    def get(self, request):
        rooms = Room.objects.all()
        serializer = RoomSerializer(rooms, many=True)
        return success_response(data=serializer.data)

    def post(self, request):
        """
        API để tạo phòng chat.
        """
        serializer = RoomSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return success_response(data=serializer.data,status_code=status.HTTP_201_CREATED)
        return failure_response(data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


class MessageListView(APIView):
    """
    API để lấy tin nhắn trong một phòng chat.
    """
    def get(self, request, room_name):
        try:
            room = Room.objects.get(name=room_name)
        except Room.DoesNotExist:
            return failure_response(message="Room not found", status_code=status.HTTP_404_NOT_FOUND)
            

        messages = Message.objects.filter(room=room).order_by('created_at')
        serializer = MessageSerializer(messages, many=True)
        return success_response(data=serializer.data)
