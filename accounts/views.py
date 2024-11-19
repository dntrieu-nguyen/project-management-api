from rest_framework.authentication import BasicAuthentication
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from accounts.serializers import LoginSerializers
from app.models import User
from user.serializers import UserSerializers
from utils.jwt import decode_token, generate_access_token, generate_refresh_token
from utils.pagination import Pagination
from utils.redis import get_cache, set_cache
from utils.response import failure_response, success_response
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import authenticate
import logging

log = logging.getLogger(__name__)

# Create your views here.
class AccountsView(APIView):
    authentication_classes = [BasicAuthentication]
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=LoginSerializers)
    def post(self, request, *args, **kwargs):  
        login_serializers = LoginSerializers(data=request.data)

        if not login_serializers.is_valid():
            return failure_response(
                message='Validation error',
                status_code=status.HTTP_400_BAD_REQUEST,
                data = login_serializers.errors
            )
       
        # print(f"access_token>> {access_token}")

        user = User.objects.filter(email=login_serializers.validated_data['email']).first()
        if not user: return failure_response(message='User not found', status_code=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(login_serializers.validated_data['password']):  
            return failure_response(message='Invalid password', status_code=status.HTTP_401_UNAUTHORIZED)


        # Create tokens
        access_token = generate_access_token(user.id, user.is_staff)
        refresh_token = generate_refresh_token(user.id)
        users = User.objects.all()

        # make pagination
        paginator = Pagination()  
        result_page = paginator.paginate_queryset(users, request)

        # store cache
        set_cache(f'access_token:{str(user.id)}', access_token, 600)

        # store refresh_token


        return success_response(
            message='Login successfully',
            status_code=status.HTTP_200_OK,
            data={
                'access_token':access_token,
                'refresh_token': refresh_token,
                'user': UserSerializers(result_page, many=True).data,
            },
            paginator=paginator
           
        )
