import json
import firebase_admin
from firebase_admin import credentials, messaging
from app.models import Firebase_tokens
from core.settings import FIREBASE

cred = credentials.Certificate(json.loads(json.dumps(FIREBASE)))
firebase_admin.initialize_app(cred)

def send_notification_to_user(user, title, content, data=None):
    """
    Gửi thông báo đến tất cả các thiết bị của người dùng.

    Args:
        user (User): Người dùng nhận thông báo.
        title (str): Tiêu đề thông báo.
        content (str): Nội dung thông báo.
        data (dict, optional): Dữ liệu bổ sung gửi kèm. Mặc định là None.
    """
 
    devices = Firebase_tokens.objects.filter(user=user, is_deleted=False)  
    tokens = [device.fcm_token for device in devices]

    if not tokens:
        print(f"No active devices for user {user.username}")
        return False


    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=content,
        ),
        data=data or {}, 
        tokens=tokens,  
    )


    try:
        response = messaging.send_multicast(message)
        print(f"Successfully sent {response.success_count} messages to {user.username}")
        return True
    except Exception as e:
        print(f"Failed to send notifications: {e}")
        return False


