from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from utils.response import success_response, failure_response
from middlewares import auth_middleware
from rest_framework import status


@swagger_auto_schema(
    method='GET',
    operation_description="Get task by id",
    tags=["Task"],
    responses={
        200: openapi.Response(
            "Success",
        ),
        400: openapi.Response(
            "Validation Error", examples={"application/json": {"error": "Invalid input"}}
        )
    },
    security=[]
)
@api_view(['GET'])
@auth_middleware
def get_task_by_id(request, id, *args, **kwargs):
    print(id)
    return success_response(status_code=status.HTTP_200_OK)
