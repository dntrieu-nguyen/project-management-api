from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import status
from utils.jwt import decode_token, generate_access_token, generate_refresh_token
from app.models import User
from user.serializers import UserSerializers
from auths.serializers import AuthSerializer, UserDataSerializer, RegisterSerializer, UpdateUserSerializer, ChangePasswordSerializer
from middlewares import auth_middleware
from utils.redis import set_cache
from utils.response import success_response, failure_response


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
@api_view(['POST'])
def login(request, *args, **kwargs):

    serializer = AuthSerializer(data=request.data)

    if not serializer.is_valid():
        raise ValidationError(serializer.errors)

    email = serializer.validated_data['email']
    password = serializer.validated_data['password']

    try:
        user = User.objects.get(email=email)
        if user.check_password(password) == False:
            return failure_response(data={"message": "Password is incorrect"}, status_code=status.HTTP_404_NOT_FOUND)

        user_data = UserSerializers(user).data

        access_token = generate_access_token(
            user_data['id'], user_data['is_staff'])
        refresh_token = generate_refresh_token(user_data['id'])
        profile = UserDataSerializer(user).data
        set_cache(f'access_token:{access_token}', access_token, 600)
        return success_response(data={'access_token': access_token, 'refresh_token': refresh_token, 'data': profile}, status_code=200)
    except User.DoesNotExist:
        return success_response(data={"message": "Not found user"}, status_code=status.HTTP_404_NOT_FOUND)


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
    operation_description="Update profile account",
    tags=["Auth"],
    request_body=UpdateUserSerializer,
    responses={
    },
    security=[{"Bearer": []}],
)
@swagger_auto_schema(
    method='GET',
    operation_description="Update profile account",
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
        user = User.objects.get(id=user_id)
        user_data = UserDataSerializer(user).data

        return Response(data=user_data, status=status.HTTP_200_OK)

    serializer = UpdateUserSerializer(data=request.data)

    if not serializer.is_valid():
        raise ValidationError(serializer.errors)

    email = serializer.validated_data['email']
    password = serializer.validated_data['password']
    first_name = serializer.validated_data['first_name']
    last_name = serializer.validated_data['last_name']

    return Response(status=status.HTTP_200_OK)


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
def change_password(request, *args, **kwargs):
    serializer = ChangePasswordSerializer(data=request.data)

    if not serializer.is_valid():
        raise ValidationError(serializer.errors)

    current_password = serializer.validated_data['current_password']
    new_password = serializer.validated_data['new_password']

    return Response(status=status.HTTP_200_OK)
