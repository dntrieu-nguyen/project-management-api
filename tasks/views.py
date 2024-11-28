from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from utils.response import success_response, failure_response
from middlewares import auth_middleware, admin_middleware
from rest_framework import status
from .serializers import GetTasksSerializer, CreateTaskSerializer, UpdateTaskSerializer
from rest_framework.exceptions import ValidationError
from app.models import Project, Task, User
from rest_framework.pagination import PageNumberPagination
from .serializers import TaskSerializer, ProjectSerializer
from django.shortcuts import get_object_or_404
from django.utils import timezone
import uuid


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
    try:
        uuid.UUID(str(id))
    except ValueError:
        return failure_response(message="Invalid UUID format", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    task = get_object_or_404(Task, id=id)
    task_data = TaskSerializer(task).data
    return success_response(data=task_data)


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
@auth_middleware
def get_tasks_by_project_id(request, *args, **kwargs):
    serializer = GetTasksSerializer(data=request.query_params)
    if not serializer.is_valid():
        raise ValidationError(serializer.errors)

    page = serializer.validated_data.get('page')
    per_page = serializer.validated_data.get('per_page')
    project_id = serializer.validated_data.get('project_id')

    project = Project.objects.get(id=project_id)
    if not project:
        return failure_response(message="Not found project", status_code=status.HTTP_404_NOT_FOUND)
    tasks = project.tasks.filter(deleted_at__isnull=True, is_deleted=False)

    paginator = PageNumberPagination()
    paginator.page_size = per_page  # Số task mỗi trang (có thể lấy từ request)
    paginated_tasks = paginator.paginate_queryset(tasks, request)

    project_data = ProjectSerializer(project).data
    tasks_data = TaskSerializer(paginated_tasks, many=True).data

    project_data['tasks'] = tasks_data
    return success_response(
        data={"project": project_data, "pagination": {
            "current_page": paginator.page.number,
            "total_pages": paginator.page.paginator.num_pages,
            "total_tasks": paginator.page.paginator.count,
        }},
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
@auth_middleware
def create_task(request, *args, **kwargs):
    serializer = CreateTaskSerializer(data=request.data)
    if not serializer.is_valid():
        raise ValidationError(serializer.errors)

    user_id = request.user['id']

    project = Project.objects.filter(id=project_id).first()
    if project is None:
        return failure_response(message="Project not found", status_code=status.HTTP_404_NOT_FOUND)

    if project.members.filter(id=user_id).first() is None:
        return failure_response(message="User not in project", status_code=status.HTTP_403_FORBIDDEN)

    project_id = serializer.validated_data.get('project_id')
    title = serializer.validated_data.get('title')
    description = serializer.validated_data.get('description')
    due_date = serializer.validated_data.get('due_date')
    member_ids = serializer.validated_data.get('members')
    task_status = serializer.validated_data.get('status')

    try:
        project = Project.objects.get(id=project_id)
        task = Task.objects.create(title=title, description=description,
                                   due_date=due_date, status=task_status, project_id=project_id)

        if member_ids is not None and len(member_ids) > 0:
            users_in_project = project.members.filter(id__in=member_ids)
            if not users_in_project.exists():
                return failure_response(message="No valid users found", status_code=status.HTTP_404_NOT_FOUND)
            task.assignees.add(*users_in_project)

        task.save()
        task_data = TaskSerializer(task).data

        return success_response(data=task_data, status_code=status.HTTP_200_OK)

    except Project.DoesNotExist:
        return failure_response(message="Not found project", status_code=status.HTTP_404_NOT_FOUND)


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
@auth_middleware
def update_task(request, *args, **kwargs):
    serializer = UpdateTaskSerializer(data=request.data)
    if not serializer.is_valid():
        raise ValidationError(serializer.errors)
    user_id = request.user['id']

    project = Project.objects.filter(id=project_id).first()
    if project is None:
        return failure_response(message="Project not found", status_code=status.HTTP_404_NOT_FOUND)

    if project.members.filter(id=user_id).first() is None:
        return failure_response(message="User not in project", status_code=status.HTTP_403_FORBIDDEN)

    task_id = serializer.validated_data.get('task_id')
    project_id = serializer.validated_data.get('project_id')
    assignee_ids = serializer.validated_data.get('members')
    title = serializer.validated_data.get('title')
    description = serializer.validated_data.get('description')
    due_date = serializer.validated_data.get('due_date')
    task_status = serializer.validated_data.get('status')

    try:
        project = Project.objects.get(id=project_id)
        task = Task.objects.get(id=task_id)
        if assignee_ids is not None:
            if len(assignee_ids) == 0:
                task.assignees.clear()
            else:
                users_in_project = project.members.filter(id__in=assignee_ids)
                if not users_in_project.exists():
                    return failure_response(message="No valid users found", status_code=status.HTTP_404_NOT_FOUND)
                task.assignees.clear()
                task.assignees.add(*users_in_project)

        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if task_status is not None:
            task.status = task_status
        if due_date is not None:
            task.due_date = due_date

        task.updated_at = timezone.now()
        task.save()
        return success_response(status_code=status.HTTP_200_OK, data=TaskSerializer(task).data)
    except Task.DoesNotExist:
        return failure_response(message="Not found task", status_code=status.HTTP_404_NOT_FOUND)
    except Project.DoesNotExist:
        return failure_response(message="Not found project", status_code=status.HTTP_404_NOT_FOUND)


@swagger_auto_schema(
    method='DELETE',
    operation_description="Delete task",
    tags=["Task"],
    manual_parameters=[
        openapi.Parameter(
            'task_id',
            openapi.IN_QUERY,
            description="The ID of the task to be deleted",
            type=openapi.TYPE_STRING,
            required=True
        ),
    ],
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
@auth_middleware
@admin_middleware
def delete_task(request, *args, **kwargs):
    user_id = request.user['id']
    task_id = request.query_params.get('task_id')
    project_id = request.query_params.get('project_id')

    if not task_id:
        return failure_response(message="task_id is required", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    if not project_id:
        return failure_response(message="project_id is required", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    project = Project.objects.filter(id=project_id).first()
    if project is None:
        return failure_response(message="Project not found", status_code=status.HTTP_404_NOT_FOUND)

    if project.members.filter(id=user_id).first() is None:
        return failure_response(message="User not in project", status_code=status.HTTP_403_FORBIDDEN)

    task = get_object_or_404(Task, id=task_id, project_id=project_id)
    task.deleted_at = timezone.now()
    task.is_deleted = True
    task.save()

    return success_response(status_code=200, data={"message": "Delete task successfully"})
