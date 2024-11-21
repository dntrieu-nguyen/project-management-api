
from rest_framework.response import Response
from rest_framework import status
from functools import wraps
from utils.jwt import decode_token
from utils.response import failure_response
import jwt


def auth_middleware(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response({'error': 'Missing or invalid Authorization header'}, status=status.HTTP_401_UNAUTHORIZED)

        token = auth_header.split(" ")[1]  # Lấy phần sau 'Bearer'

        if not token:
            return Response({'error': 'Access token missing'}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            decoded = jwt.decode(
                token,
                key='django_app_secret_key',
                algorithms=["HS256"],
                options={"verify_exp": True},
            )

            request.user = {
                "id": decoded.get("id"),
                "role": decoded.get("role"),
            }

            return view_func(request, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return failure_response(message="Token expire")
        except jwt.InvalidTokenError as e:
            return failure_response(message="Token invalid")

    return wrapper