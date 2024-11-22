
from rest_framework.response import Response
from rest_framework import status
from functools import wraps
from utils.jwt import decode_token
from utils.response import failure_response
import jwt
from utils.redis import get_cache
from core.settings import JWT_SECRET


def auth_middleware(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith("Bearer "):
            return failure_response(message="Missing or invalid Authorization header", status_code=status.HTTP_401_UNAUTHORIZED)

        token = auth_header.split(" ")[1]  # Lấy phần sau 'Bearer'

        if not token:
            return failure_response(message="Access token missing", status_code=status.HTTP_401_UNAUTHORIZED)
        try:
            if get_cache(f'access_token:{token}') == None:
                return failure_response(message="Invalid token", status_code=status.HTTP_401_UNAUTHORIZED)

            decoded = jwt.decode(
                token,
                key=JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_exp": True},
            )

            request.user = {
                "id": decoded.get("id"),
                "role": decoded.get("role"),
            }

            return view_func(request, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return failure_response(message="Token expire", status_code=status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError as e:
            return failure_response(message="Token invalid", status_code=status.HTTP_401_UNAUTHORIZED)

    return wrapper
