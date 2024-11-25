from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

# Success Response Utility
def success_response(data: dict = None, message: str = "Operation successful", status_code: int = status.HTTP_200_OK, paginator=None):
    if paginator and isinstance(paginator, PageNumberPagination):
        return paginator.get_paginated_response(data)
    response_data = {
        "success": True,
        "message": message,
        "data": data if data is not None else None
    }
    if paginator is not None:
        response_data["pagination"] = paginator
    return Response(
        response_data,
        status=status_code
    )

# Failure Response Utility
def failure_response(message: str, status_code: int = status.HTTP_400_BAD_REQUEST, data: dict = None):
    return Response(
        {
            "success": False,
            "message": message,
            "data": data or None,
        },
        status=status_code
    )