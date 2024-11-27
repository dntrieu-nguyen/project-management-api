import datetime
from django.shortcuts import render
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from app.models import User
from middlewares import auth_middleware
from notifications.serializers import NotificationRequestUpdateStatusSerializers, NotificationsRequestByUserIdSerializers, NotificationsRequestCreateSerializers
from utils.response import failure_response, success_response
from firebase.firebase_config import db

@api_view(['GET'])
def get_all_notifications_by_user(request):
    """
    Lấy tất cả thông báo của người dùng dựa trên ID.
    """
    # Sử dụng query parameters thay vì request.data cho GET request
    user_id = request.data['id']
    
    if not user_id:
        return failure_response(
            message='Validation Errors',
            data={'id': ['This field is required.']}
        )

    ref = db.reference(f'notifications/{user_id}')
    snapshot = ref.get()

    if not snapshot:
        return failure_response(
            message='No notifications found',
            data=snapshot
        )

    return success_response(message='successfully', data=snapshot)


@api_view(['POST'])
@auth_middleware
def send_notifications_to_user(request):
    """
    Gửi thông báo đến một người dùng.
    """
    req_body = NotificationsRequestCreateSerializers(data=request.data)
    sender = request.user

    if not req_body.is_valid():
        return failure_response(
            message="Validation errors",
            data=req_body.errors
        )
    
     # check existed sender
    is_existed_sender = User.objects.filter(id=sender['id'])

    if not is_existed_sender:
        return failure_response(message="sender not found")
    
    receiver = User.objects.filter(id=req_body.validated_data['user_id'])

    if not receiver:
        return failure_response(message="user not found")
    
    req_body.validated_data['sender_id'] = sender['id'].replace('-','')
    req_body.validated_data['created_at'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    user_id = req_body.validated_data['user_id']
    ref = db.reference(f'notifications/{user_id}')
    snapshot = ref.push(req_body.validated_data) 

    return success_response(
        message="Notification sent successfully",
        data={"notification_id": snapshot.key} 
    )

@api_view(['PUT'])
@auth_middleware
def update_status_notifications(request):
    req_body = NotificationRequestUpdateStatusSerializers(data=request.data)
    user_id = request.user['id']


    if not req_body.is_valid():
        return failure_response(
            message="Validation Errors",
            data=req_body.errors
        )

 
    notification_ref = db.reference(f'notifications/{str(user_id).replace('-', '')}/{req_body.validated_data["notification_id"]}')
    current_data = notification_ref.get() 

    if not current_data:
        return failure_response(message="Notification not found")

   
    update_data = {
        'is_read': True,
        'updated_at': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    }

 
    notification_ref.update(update_data)

 
    detail_notification_snapshot = notification_ref.get()

    return success_response(message='Notification updated successfully', data=detail_notification_snapshot)
