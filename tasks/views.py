from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from utils.response import success_response, failure_response
from middlewares import auth_middleware
from rest_framework import status
from .serializers import GetTasksSerializer, CreateTaskSerializer, UpdateTaskSerializer


@swagger_auto_schema(
    method='GET',
    operation_description="Get task by id",
    tags=["Task"],
    responses={
        200: openapi.Response(
            "Success",
        ),
        400: openapi.Response(
            "Validation Error", examples=None
        )
    },
    security=[]
)
@api_view(['GET'])
@auth_middleware
def get_task_by_id(request, id, *args, **kwargs):
    print(id)
    return success_response(status_code=status.HTTP_200_OK)


@swagger_auto_schema(
    method='GET',
    operation_description="Get tasks by project_id with pagination",
    tags=["Task"],

    responses={
        200: openapi.Response(
            "Success",
            examples=None
        ),
        400: openapi.Response(
            "Validation Error", examples=None
        )
    },
    security=[]
)
@api_view(['GET'])
def get_tasks_by_project_id(request, *args, **kwargs):
    serializer = GetTasksSerializer(data=request.query_params)
    if not serializer.is_valid():
        raise failure_response(data=serializer.errors,
                               status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    page = serializer.validated_data.get('page')
    per_page = serializer.validated_data.get('per_page')
    project_id = serializer.validated_data.get('project_id')

    return success_response(
        data={"tasks": [], "page": page,
              "per_page": per_page, "project_id": project_id},
        status_code=status.HTTP_200_OK
    )


@swagger_auto_schema(
    method='POST',
    operation_description="Create task",
    tags=["Task"],
    request_body=CreateTaskSerializer,
    responses={
        200: openapi.Response(
            "Success",
            examples=None
        ),
        400: openapi.Response(
            "Validation Error", examples=None
        )
    },
    security=[]
)
@api_view(['POST'])
def create_task(request, *args, **kwargs):
    serializer = CreateTaskSerializer(data=request.data)
    if not serializer.is_valid():
        raise failure_response(data=serializer.errors,
                               status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    return success_response(

        status_code=status.HTTP_200_OK
    )


@swagger_auto_schema(
    method='PATCH',
    operation_description="Update task",
    tags=["Task"],
    request_body=UpdateTaskSerializer,
    responses={
        200: openapi.Response(
            "Success",
            examples=None
        ),
        400: openapi.Response(
            "Validation Error", examples=None
        )
    },
    security=[]
)
@api_view(['PATCH'])
def update_task(request, task_id, *args, **kwargs):
    serializer = UpdateTaskSerializer(data=request.data)
    if not serializer.is_valid():
        raise failure_response(data=serializer.errors,
                               status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    return success_response(status_code=status.HTTP_200_OK)


@swagger_auto_schema(
    method='DELETE',
    operation_description="Delete task",
    tags=["Task"],
    request_body=UpdateTaskSerializer,
    responses={
        200: openapi.Response(
            "Success",
            examples=None
        ),
        400: openapi.Response(
            "Validation Error", examples=None
        )
    },
    security=[]
)
@api_view(['DELETE'])
def delete_task(request, task_id, *args, **kwargs):
    return success_response(status_code=200)
