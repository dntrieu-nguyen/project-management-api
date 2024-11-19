from django.forms import ValidationError
from django.http import Http404
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, APIException
from rest_framework import status
from django.utils.deprecation import MiddlewareMixin
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

class ExceptionHandlingMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        # Handle ValidationError
        if isinstance(exception, ValidationError):
            errors = exception.message_dict if hasattr(exception, "message_dict") else str(exception)
            return Response(
                {
                    "success": False,
                    "message": "Validation error",
                    "data": errors
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        # Handle NotFound
        elif isinstance(exception, (Http404, NotFound)):
            return Response(
                {
                    "success": False,
                    "message": "Resource not found",
                    "data": None
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Handle APIException
        elif isinstance(exception, APIException):
            errors = str(exception.detail) if not isinstance(exception.detail, dict) else exception.detail
            return Response(
                {
                    "success": False,
                    "message": "API error",
                    "data": errors
                },
                status=exception.status_code
            )

        # Handle ValueError
        elif isinstance(exception, ValueError):
            return Response(
                {
                    "success": False,
                    "message": str(exception),
                    "data": None
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Handle other exceptions
        else:
            return Response(
                {
                    "success": False,
                    "message": "Internal server error",
                    "data": None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )