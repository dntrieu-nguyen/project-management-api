from rest_framework import serializers


class NotificationsRequestByUserIdSerializers(serializers.Serializer):
    id = serializers.CharField(required = True)

class NotificationsRequestCreateSerializers(serializers.Serializer):
    user_id = serializers.CharField(required=True)
    title = serializers.CharField(required = True)
    content = serializers.CharField()
    is_read = serializers.BooleanField(default = False)

class NotificationRequestUpdateStatusSerializers(serializers.Serializer):
    notification_id = serializers.CharField(required=True)