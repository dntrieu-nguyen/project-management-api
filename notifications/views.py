import datetime
from uuid import UUID
from django.shortcuts import render
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from app.models import User
from middlewares import auth_middleware
from notifications.serializers import  NotificationsRequestCreateSerializers
from utils.response import failure_response, success_response
from firebase.firebase_config import db
from rest_framework import status

@api_view(['GET'])
@auth_middleware
def get_all_notifications_by_user(request):
    """
    Lấy tất cả thông báo của người dùng dựa trên ID.
    """
    user_id = request.user['id']

    ref = db.reference(f"notifications/{user_id}")

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
    req_body = NotificationsRequestCreateSerializers(data=request.data)
    sender = request.user

    if not req_body.is_valid():
        return failure_response(
            message="Validation errors",
            data=req_body.errors
        )
    
    # Check existed sender
    if not User.objects.filter(id=sender['id']).exists():
        return failure_response(message="sender not found")
    
    receiver = User.objects.filter(id=req_body.validated_data['user_id']).first()
    if not receiver:
        return failure_response(message="user not found")
    
    notification_data = req_body.validated_data
    notification_data['sender_id'] = sender['id']
    notification_data['created_at'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    notification_data['updated_at'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    
    user_id = notification_data['user_id']
    ref = db.reference(f"notifications/{UUID(user_id)}")
    
    # Uncomment the following line if you need to save the notification
    snapshot = ref.push(notification_data) 

    return success_response(
        message="Notification sent successfully",
        # Uncomment this line if you need to return the notification ID
        data={"notification_id": snapshot.key}
    )

@api_view(['PATCH'])
@auth_middleware
def seen_notification_by_user(request):
    try:
        user_id = request.user['id']

        notification_id = request.query_params['notification_id']

        if not bool(notification_id):
            return failure_response(
                message="Validation errors",
                data= {
                    "notification_id": "required"
                }
            )

        ref = db.reference(f"notifications/{user_id}/{notification_id}")

        ref.update({
            "is_read":True,
            "updated_at": datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        })

        return success_response(message="update successfully")
    except Exception as e:
        return failure_response(
           message=str(e),
           status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )