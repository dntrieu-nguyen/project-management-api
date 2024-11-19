from rest_framework.authentication import BasicAuthentication
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from accounts.serializers import LoginSerializers
from utils.response import failure_response, success_response
from drf_yasg.utils import swagger_auto_schema

import logging

log = logging.getLogger(__name__)

# Create your views here.
class AccountsView(APIView):
    authentication_classes = [BasicAuthentication]
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=LoginSerializers)
    def post(self, request, *args, **kwargs):  
        login_serializers = LoginSerializers(data=request.data)

        # Kiểm tra tính hợp lệ của serializer
        if not login_serializers.is_valid():
            return failure_response(
                message='Validation error',
                status_code=status.HTTP_400_BAD_REQUEST,
                data = login_serializers.errors
            )
        

        return success_response(
            message='Login successfully',
            status_code=status.HTTP_200_OK,
            data=login_serializers.data
        )
