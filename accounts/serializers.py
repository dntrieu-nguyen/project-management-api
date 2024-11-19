from rest_framework import serializers

class LoginSerializers(serializers.Serializer):
    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True)