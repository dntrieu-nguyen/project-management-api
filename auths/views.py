from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import status
from utils.jwt import decode_token, generate_access_token, generate_refresh_token
from app.models import User, RefreshToken
from user.serializers import UserSerializers
from auths.serializers import AuthSerializer, LogoutSerializer, UserDataSerializer, RegisterSerializer, UpdateUserSerializer, ChangePasswordSerializer, RefreshTokenSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
from middlewares import auth_middleware
from utils.redis import remove_cache, set_cache, get_cache
from utils.response import success_response, failure_response
import jwt
from datetime import datetime, timedelta, timezone
from utils.send_mail import send_email
import random
from django.template.loader import render_to_string
from django_ratelimit.decorators import ratelimit


@swagger_auto_schema(
    method='POST',
    operation_description="Login by Email",
    tags=["Auth"],
    request_body=AuthSerializer,
    responses={
        200: openapi.Response(
            "Success", examples={"application/json": {"message": "Hello world"}}
        ),
        400: openapi.Response(
            "Validation Error", examples={"application/json": {"error": "Invalid input"}}
        )
    },
    security=[]
)
@ratelimit(key='ip', rate="1/m", block=False)
@api_view(['POST'])
def login(request, *args, **kwargs):
    serializer = AuthSerializer(data=request.data)

    if not serializer.is_valid():
        return failure_response(
            message="Validation errors",
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    email = serializer.validated_data['email']
    password = serializer.validated_data['password']

    try:
        # Kiểm tra user tồn tại
        user = User.objects.get(email=email)

        # Kiểm tra mật khẩu
        if not user.check_password(password):
            return failure_response(
                message="Password is incorrect",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        # Tạo token và cookie
        user_data = UserSerializers(user).data
        access_token = generate_access_token(
            user_data['id'], user_data['is_staff'])
        refresh_token = generate_refresh_token(user_data['id'])
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        # Lưu Refresh Token
        RefreshToken.objects.create(
            user=user, expires_at=expires_at, token=refresh_token)

        # Dữ liệu phản hồi
        profile = UserDataSerializer(user).data
        set_cache(f"access_token:{access_token}", access_token, 6000)

        response = success_response(
            data={
                'access_token': access_token,
                'refresh_token': refresh_token,
                'data': profile
            },
            status_code=status.HTTP_200_OK
        )

        # Cài đặt cookie
        response.set_cookie(
            key="refresh_token_server",
            value=str(refresh_token),
            httponly=True,
            secure=True,
            max_age=30*24*60*60,
        )

        return response

    except User.DoesNotExist:
        return failure_response(
            message="User not found",
            status_code=status.HTTP_404_NOT_FOUND
        )


@swagger_auto_schema(
    method='POST',
    operation_description="Register account",
    tags=["Auth"],
    request_body=RegisterSerializer,
    responses={
    },
    security=[]
)
@api_view(['POST'])
def register(request, *args, **kwargs):
    serializer = RegisterSerializer(data=request.data)

    if not serializer.is_valid():
        raise ValidationError(serializer.errors)

    email = serializer.validated_data['email']
    password = serializer.validated_data['password']
    first_name = serializer.validated_data['first_name']
    last_name = serializer.validated_data['last_name']
    user_name = serializer.validated_data['user_name']

    user = User.objects.filter(email=email).first()
    if user:
        return failure_response(message='Email is existed', status_code=status.HTTP_409_CONFLICT)

    new_user = User(
        email=email,
        is_staff=False,
        first_name=first_name,
        last_name=last_name,
        username=user_name
    )

    new_user.set_password(password)
    new_user.save()
    new_user_data = UserSerializers(new_user).data

    return success_response(data=new_user_data)


@swagger_auto_schema(
    method='PATCH',
    operation_description="Update profile",
    tags=["Auth"],
    request_body=UpdateUserSerializer,
    responses={
    },
    security=[{"Bearer": []}],
)
@swagger_auto_schema(
    method='GET',
    operation_description="Get profile",
    tags=["Auth"],
    responses={
    },
    security=[{"Bearer": []}],
)
@api_view(['GET', 'PATCH'])
@auth_middleware
def profile_view(request, *args, **kwargs):

    user_id = request.user['id']

    if request.method == 'GET':

        user = User.objects.filter(id=user_id).first()
        if not user:
            return failure_response(message='Not found User', status_code=status.HTTP_404_NOT_FOUND)
        user_data = UserDataSerializer(user).data

        return Response(data=user_data, status=status.HTTP_200_OK)

    if request.method == "PATCH":
        serializer = UpdateUserSerializer(data=request.data)
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)

        first_name = serializer.validated_data['first_name']
        last_name = serializer.validated_data['last_name']
        username = serializer.validated_data['username']

        user = User.objects.filter(id=user_id).first()
        if not user:
            return failure_response(message="Not found user", status_code=status.HTTP_404_NOT_FOUND)

        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        user.save()

        return Response(status=status.HTTP_200_OK, data=UserDataSerializer(user).data)


@swagger_auto_schema(
    method='PATCH',
    operation_description="Change password",
    tags=["Auth"],
    request_body=ChangePasswordSerializer,
    responses={
    },
    security=[{"Bearer": []}],
)
@api_view(['PATCH'])
@auth_middleware
def change_password(request, *args, **kwargs):
    serializer = ChangePasswordSerializer(data=request.data)

    if not serializer.is_valid():
        raise ValidationError(serializer.errors)

    user_id = request.user['id']
    current_password = serializer.validated_data['current_password']
    new_password = serializer.validated_data['new_password']
    refresh_token = serializer.validated_data['refresh_token']

    try:
        decoded = decode_token(refresh_token)
    except jwt.ExpiredSignatureError:
        return failure_response(message="Refresh Token expire", status_code=status.HTTP_401_UNAUTHORIZED)
    except jwt.InvalidTokenError as e:
        return failure_response(message="Refresh Token invalid", status_code=status.HTTP_401_UNAUTHORIZED)

    user = User.objects.filter(id=user_id).first()
    if not user:
        return failure_response(message='User not found', status_code=status.HTTP_401_UNAUTHORIZED)

    if not user.check_password(current_password):
        return failure_response(message='Current password is incorrect', status_code=status.HTTP_404_NOT_FOUND)

    old_refresh_token = RefreshToken.objects.filter(user_id=user_id).first()
    old_refresh_token.token = generate_refresh_token(user_id)
    old_refresh_token.save()

    user.set_password(new_password)
    user.save()

    user_data = UserSerializers(user).data
    user_data['password'] = new_password

    return success_response(status=status.HTTP_200_OK, data=user_data)


@swagger_auto_schema(
    method='POST',
    operation_description="Refresh access token",
    request_body=RefreshTokenSerializer,
    tags=["Auth"],
    responses={
    },
    security=[{"Bearer": []}],
)
@api_view(['POST'])
def refresh_token(request, *args, **kwargs):
    serializer = RefreshTokenSerializer(data=request.data)

    if not serializer.is_valid():
        raise ValidationError(serializer.errors)
    refresh_token = serializer.validated_data['refresh_token']

    old_refresh_token = RefreshToken.objects.filter(
        token=refresh_token).first()
    if not old_refresh_token:
        return failure_response(status_code=status.HTTP_401_UNAUTHORIZED, message="Invalid refresh token")

    try:
        decoded = decode_token(refresh_token)
        user = User.objects.filter(id=decoded['id']).first()
        new_access_token = generate_access_token(
            id=decoded['id'], role=user.is_staff)
        set_cache(f"access_token:{new_access_token}", new_access_token, 6000)

        return success_response(status_code=200, data={"new_access_token": new_access_token})
    except jwt.ExpiredSignatureError:
        return failure_response(message="Refresh Token expire", status_code=status.HTTP_401_UNAUTHORIZED)
    except jwt.InvalidTokenError as e:
        return failure_response(message="Refresh Token invalid", status_code=status.HTTP_401_UNAUTHORIZED)


@swagger_auto_schema(
    method='POST',
    operation_description="Forgot password",
    tags=["Auth"],
    request_body=ForgotPasswordSerializer(),
    responses={
        200: openapi.Response(
            "Success",
            examples=None
        ),
        400: openapi.Response(
            "Validation Error", examples=None
        )
    },
    security=[]
)
@api_view(['POST'])
def forgot_password(request, *args, **kwargs):
    serializer = ForgotPasswordSerializer(data=request.data)
    if not serializer.is_valid():
        raise ValidationError(serializer.errors)
    email = serializer.validated_data.get('email')
    user = User.objects.filter(email=email).first()
    if not user:
        return failure_response(status_code=status.HTTP_404_NOT_FOUND, message="Not found user")

    random_number = random.randint(10000, 99999)
    set_cache(f"forgot_pass:{email}", random_number, 300)

    subject = "Welcome to Django App"
    txt_ = "Thank you for signing up."
    from_email = user.email
    recipient_list = user.email
    html_ = render_to_string('forgot_password.html', {
        'secret_key': str(random_number)
    })

    result = send_email(subject, txt_, from_email, recipient_list, html_)

    return success_response(data={"message": 'Send mail successfully', 'email': email})


@swagger_auto_schema(
    method='POST',
    operation_description="Reset password",
    tags=["Auth"],
    request_body=ResetPasswordSerializer(),
    responses={
        200: openapi.Response(
            "Success",
            examples=None
        ),
        400: openapi.Response(
            "Validation Error", examples=None
        )
    },
    security=[]
)
@api_view(['POST'])
def reset_password(request, *args, **kwargs):
    serializer = ResetPasswordSerializer(data=request.data)
    if not serializer.is_valid():
        raise ValidationError(serializer.errors)

    secret_key = serializer.validated_data.get('secret_key')
    email = serializer.validated_data.get('email')

    isExist = get_cache(f"forgot_pass:{email}")
    if isExist == None:
        return failure_response(message="Not found secret key", status_code=status.HTTP_404_NOT_FOUND)
    if str(secret_key) != str(isExist):
        return failure_response(message="Secret key not valid", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    new_password = serializer.validated_data.get('new_password')
    user = User.objects.filter(email=email).first()
    if user is None:
        return failure_response(message="Not found user", status_code=status.HTTP_404_NOT_FOUND)
    user.set_password(new_password)
    user.save()
    user_data = UserDataSerializer(user).data
    return success_response(data=user_data)


@api_view(['POST'])
@auth_middleware
def logout(request):
    try:
        access_token = request.user['access_token']

        req_body = LogoutSerializer(data=request.data)
        if not req_body.is_valid():
            return failure_response(
                message="Validation Errors",
                data=req_body.errors
            )
        valid_data = req_body.validated_data

    # Remove token
        remove_cache(f"access_token:{access_token}")
        refresh_token = RefreshToken.objects.get(
            token=valid_data['refresh_token'])
        refresh_token.delete()

        return success_response(
            message="Logout successfully"
        )
    except Exception as e:
        return failure_response(
            message="An unexpected error occurred",
            data=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
