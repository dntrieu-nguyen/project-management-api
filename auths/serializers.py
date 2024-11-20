
from app.models import User
from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True, required=True, min_length=6)
    first_name = serializers.CharField(required=True, min_length=6)
    last_name = serializers.CharField(required=True, min_length=6)


class UpdateUserSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False, min_length=6,)
    last_name = serializers.CharField(required=False, min_length=6)
    username = serializers.CharField(required=False, min_length=6)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        write_only=True, required=True, min_length=6)
    new_password = serializers.CharField(
        write_only=True, required=True, min_length=6)


class AuthSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True, required=True, min_length=6)


class UserDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name',
                  'last_name', 'email', 'date_joined']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Dynamically hide certain fields
        request = self.context.get('request')
        if request and not request.user.is_staff:  # Example condition
            data.pop('date_joined', None)
        return data
