
from rest_framework.response import Response
from rest_framework import status
from functools import wraps


def auth_middleware(view_func):
    @wraps(view_func)
    def wrapper(view, request, *args, **kwargs):
        # Lấy header Authorization
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response({'error': 'Missing or invalid Authorization header'}, status=status.HTTP_401_UNAUTHORIZED)

        # Tách token từ header
        token = auth_header.split(" ")[1]  # Lấy phần sau 'Bearer'
        if not token:
            return Response({'error': 'Access token missing'}, status=status.HTTP_401_UNAUTHORIZED)

        # (Optional) Thực hiện kiểm tra token nếu cần
        if token != "YOUR_SECRET_ACCESS_TOKEN":
            return Response({'error': 'Invalid access token'}, status=status.HTTP_403_FORBIDDEN)

        # Nếu hợp lệ, tiếp tục xử lý request
        return view_func(view, request, *args, **kwargs)
    return wrapper
