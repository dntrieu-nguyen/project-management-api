from django.shortcuts import render
from rest_framework.authentication import BasicAuthentication
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from accounts.serializers import LoginSerializers
from app.models import User, Firebase_tokens
from notifications.FCMManage import send_notification_to_user
from user.serializers import UserSerializers
from utils.jwt import generate_access_token, generate_refresh_token
from utils.response import failure_response, success_response
from datetime import datetime

class AccountsView(APIView):
    authentication_classes = [BasicAuthentication]
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):  
        login_serializers = LoginSerializers(data=request.data)

        if not login_serializers.is_valid():
            return failure_response(
                message='Validation error',
                status_code=status.HTTP_400_BAD_REQUEST,
                data=login_serializers.errors
            )

        # Lấy thông tin user
        user = User.objects.filter(email=login_serializers.validated_data['email']).first()
        if not user:
            return failure_response(message='User not found', status_code=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(login_serializers.validated_data['password']):  
            return failure_response(message='Invalid password', status_code=status.HTTP_401_UNAUTHORIZED)

        # Lấy FCM token và device_name từ request
        fcm_token = request.data.get('fcm_token')
        device_name = request.data.get('device_name', 'Unknown Device')

        if fcm_token:
            # Thêm hoặc cập nhật token vào Firebase_tokens
            Firebase_tokens.objects.update_or_create(
                user=user,
                fcm_token=fcm_token,
                defaults={
                    'device_name': device_name,
                    'last_active': datetime.now()
                }
            )

        # Tạo JWT token
        access_token = generate_access_token(user.id, user.is_staff)
        refresh_token = generate_refresh_token(user.id)

        # Gửi thông báo chào mừng
        send_notification_to_user(
            user=user,
            title="Welcome Back!",
            content="You have successfully logged in.",
            data={"action": "login"}
        )

        return success_response(
            message='Login successfully',
            status_code=status.HTTP_200_OK,
            data={
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': UserSerializers(user).data
            }
        )


def test_view(request):
    return render(request, 'test_notification.html')