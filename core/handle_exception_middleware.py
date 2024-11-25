import logging
from django.http import Http404
from rest_framework.exceptions import NotFound, APIException
from rest_framework import status
from django.core.exceptions import ValidationError
from rest_framework.response import Response

from utils.response import failure_response




class ExceptionHandlingMiddleware:
    def process_exception(self, request, exception):
        """
        Handle different types of exceptions and return a standardized response.
        """
        # Validation Error (Django & DRF)
        if isinstance(exception, ValidationError):
            errors = (
                exception.message_dict
                if hasattr(exception, "message_dict")
                else exception.detail
                if hasattr(exception, "detail")
                else str(exception)
            )
            return failure_response(
                message="Validation error",
                data=errors,
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # Not Found (Http404 or DRF NotFound)
        if isinstance(exception, (Http404, NotFound)):
            return failure_response(
                message="Resource not found",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # APIException (custom errors in DRF)
        if isinstance(exception, APIException):
            errors = (
                exception.detail
                if isinstance(exception.detail, dict)
                else str(exception.detail)
            )
            return failure_response(
                message="API error",
                data=errors,
                status_code=exception.status_code,
            )

        # Generic ValueError
        if isinstance(exception, ValueError):
            return failure_response(
                message=str(exception),
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Unhandled exceptions (Internal Server Error)
        return failure_response(
            message="Internal server error",
            data=str(exception),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
