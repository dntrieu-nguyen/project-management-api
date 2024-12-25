
from app.models import User
from rest_framework import serializers

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True, required=True, min_length=6
    )
    first_name = serializers.CharField(required=True, min_length=4)
    last_name = serializers.CharField(required=True, min_length=4)
    user_name = serializers.CharField(required=True, min_length=8)

    def validate_password(self, value):

        if len(value) < 6:
            raise serializers.ValidationError(
                "Password must be at least 6 characters long.")
        return value


class UpdateUserSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False, min_length=4,)
    last_name = serializers.CharField(required=False, min_length=4)
    username = serializers.CharField(required=False, min_length=6)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        write_only=True, required=True, min_length=6)
    new_password = serializers.CharField(
        write_only=True, required=True, min_length=6)
    refresh_token = serializers.CharField()


class AuthSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True, required=True, min_length=6)


class UserDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name',
                  'last_name', 'email', 'date_joined', 'is_staff']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Dynamically hide certain fields
        request = self.context.get('request')
        if request and not request.user.is_staff:  # Example condition
            data.pop('date_joined', None)
        return data


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True, min_length=6,)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    secret_key = serializers.CharField(
        min_length=1, max_length=5, required=True)
    new_password = serializers.CharField(
        write_only=True, required=True, min_length=6)

class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()