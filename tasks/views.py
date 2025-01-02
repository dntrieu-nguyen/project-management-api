import datetime
import json
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from utils.pagination import Pagination
from utils.response import success_response, failure_response
from middlewares import auth_middleware, admin_middleware
from rest_framework import status
from .serializers import GetTasksSerializer, CreateTaskSerializer, ResponseSerializers, SendNotificationSerializers, UpdateTaskSerializer
from rest_framework.exceptions import ValidationError
from app.models import Project, Task, User
from rest_framework.pagination import PageNumberPagination
from .serializers import TaskSerializer, ProjectSerializer
from django.shortcuts import get_object_or_404
from django.utils import timezone
import uuid
from firebase.firebase_config import db
from django.db.models import Q


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

    paginator = Pagination()
    paginated_tasks = paginator.paginate_queryset(tasks, request)

    project_data = ProjectSerializer(project).data
    tasks_data = TaskSerializer(paginated_tasks, many=True).data

    project_data['tasks'] = tasks_data
    return success_response(
        data={"project": project_data},
        paginator=paginator
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
    try:
        req_body = CreateTaskSerializer(data=request.data)
        if not req_body.is_valid():
            return failure_response(
                message="Validation Errors",
                data= req_body.errors
            )

        user_id = request.user['id']
        valid_data = req_body.validated_data


        project_id = valid_data.get('project_id')

        project = Project.objects.filter(id=project_id).first()

        user = User.objects.filter(id= user_id).first()

        if project is None:
            return failure_response(message="Project not found", status_code=status.HTTP_404_NOT_FOUND)
       
 
        assignee_ids = valid_data.get('assignees', [])

        project_member_ids = set(project.members.values_list('id', flat=True))

        invalid_assignees = [assignee_id for assignee_id in assignee_ids if assignee_id not in project_member_ids]

        if invalid_assignees:
            return failure_response(
                message=f"These users are not in the project: {invalid_assignees}",
                status_code=status.HTTP_403_FORBIDDEN,
            )


        new_task = Task.objects.create(
            title = valid_data['title'],
            description = valid_data['description'],
            start_date = valid_data['start_date'],
            end_date = valid_data['end_date'],
            status = valid_data['status'],
            priority = valid_data['priority'],
            estimate_hour = valid_data['estimate_hour'],
            actual_hour = valid_data['actual_hour']
        )

        project.tasks.add(new_task)

        for mem in assignee_ids:
            ref = db.reference(f'invitedNotifications/{mem}')
            new_data = {
                    "project": str(project.id),
                    "task": str(new_task.id),
                    "status": "pending",
                    "from": user.email,
                    "type":"invite",
                    "context":"task",
                    "message": f"You have a invitation to join task {new_task.title} from {user.email}",
                    "created_at" : datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                }
            ref.push(new_data)
        
        return success_response(
            message="Task created successfully",
           
        )

    except Exception as e:
      return failure_response(
            message="An unexpected error occurred",
            data=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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
@auth_middleware
def update_task(request, *args, **kwargs):
    serializer = UpdateTaskSerializer(data=request.data)
    if not serializer.is_valid():
        return failure_response(
            message="Validation errors",
            data=serializer.errors
        )

    task_id = serializer.validated_data.get('task_id')
    project_id = serializer.validated_data.get('project_id')
    assignee_ids = serializer.validated_data.get('members')
    title = serializer.validated_data.get('title')
    description = serializer.validated_data.get('description')
    due_date = serializer.validated_data.get('due_date')
    task_status = serializer.validated_data.get('status')
    estimate_hour = serializer.validated_data.get('estimate_hour')
    actual_hour = serializer.validated_data.get('actual_hour')
    priority = serializer.validated_data.get('priority')

    user_id = request.user['id']
    user = User.objects.get(id=user_id)

    try:
        # Fetch the project and task at the same time
        project = Project.objects.get(id=project_id)
        task = Task.objects.get(id=task_id)

        # Check if the user is a member of the project
       
        # Update assignees if provided
        if assignee_ids is not None:
            if len(assignee_ids) == 0:
                task.assignees.clear()
            else:      
                for mem in assignee_ids:
                    ref = db.reference(f'invitedNotifications/{mem}')
                    # check if member is already in the task
                    if task.assignees.filter(id=mem).exists():
                    # Create a new notification only for unassigned users
                        new_data = {
                            "project": str(project.id),
                            "task": str(task.id),
                            "status": "pending",
                            "from": user.email,
                            "type": "invite",
                            "context": "task",
                            "message": f"You have an invitation to join task {task.title} from {user.email}",
                            "created_at": datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                        }
                        ref.push(new_data)

                    if mem == user_id:
                        ref = db.reference(f'notifications/{mem}')
                        task.assignees.add(user)

                        new_notification = {
                            "title": f"{task.title}",
                            "content": f"you has joined {task.title}",
                            "is_read": False,
                            "sender_id": user_id,
                            "created_at": datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                            "updated_at": datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                        }

                        ref.push(new_notification)
                
        # Update task fields if provided
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if task_status is not None:
            task.status = task_status
        if due_date is not None:
            task.due_date = due_date
        if estimate_hour is not None:
            task.estimate_hour = estimate_hour
        if actual_hour is not None:
            task.actual_hour = actual_hour
        if priority is not None:
            task.priority = priority

        # Save the task
        task.updated_at = timezone.now()
        task.save()

        return success_response(status_code=status.HTTP_200_OK, data=TaskSerializer(task).data)

    except Task.DoesNotExist:
        return failure_response(message="Task not found", status_code=status.HTTP_404_NOT_FOUND)
    except Project.DoesNotExist:
        return failure_response(message="Project not found", status_code=status.HTTP_404_NOT_FOUND)


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

@api_view(['POST'])
@auth_middleware
def send_invite_join_task(request):
    try:
      user_id = request.user['id']
      ref = db.reference(f"invitedNotifications/{user_id}")

      user = User.objects.get(id=user_id)

      req_body = SendNotificationSerializers(data=request.data)
      if not req_body.is_valid():
        return failure_response(
              message="Validation errors",
              data = req_body.errors
          )
      validated_data = req_body.validated_data

      task = Task.objects.get(id = uuid.UUID(validated_data['task_id']))

        # check task existance
      if task is None:
          return failure_response(
              message="task not found",
             
          )
      new_data = {
          "task": str(task.id),
          "project": str(validated_data['project_id']),
          "status": "pending",
          "type":"invite",
          "context" :"task",
          "from": user.email,
          "message": f"You have a invitation to join {task.title} from {user.email}",
          "created_at" : datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
      }
      snapshot = ref.push(new_data)
      return success_response(
          message="Send invitation successfully",
      )
    except Exception as e:
      return failure_response(
            message="An unexpected error occurred",
            data=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@auth_middleware
def accept_invitation(request):
    try:
      user_id = request.user['id']
      ref = db.reference(f"invitedNotifications/{user_id}")

      req_body = ResponseSerializers(data=request.data)

      if not req_body.is_valid():
        return failure_response(
            message="Validation erros",
            data= req_body.errors
        )
      valid_data = req_body.validated_data
      
      task = Task.objects.filter(id=valid_data['task_id']).first()
      user = User.objects.filter(id = user_id).first()

      if not task:
          return failure_response(
              message="Task not found",
              status_code= status.HTTP_404_NOT_FOUND
          )
      
      if task.assignees.filter(id = user_id).exists():
          return failure_response(
              message="User is already a member of this task"
          )
      task.assignees.add(user)

      notification = ref.child(valid_data['notification_id'])
      member_ids = task.assignees.exclude(id=user_id)

      for member in member_ids:
          ref_member = db.reference(f"notifications/{str(member)}")
          new_notification = {
            "title": f"{task.title}",
            "content" : f"{user.email} has joined {task.title}",
            "is_read": False,
            "sender_id": user_id,
            "created_at": datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            "updated_at":datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            }
          ref_member.push(new_notification)

      notification.delete()
      return success_response(
        message=f"User {user.email} has been successfully added to project {task.title}.",
        status_code=status.HTTP_200_OK
      )

    except Exception as e:
      return failure_response(
            message="An unexpected error occurred",
            data=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@auth_middleware
def decline_invitation(request):
    try:
        user_id = request.user.get('id')
        ref = db.reference(f"invitedNotifications/{user_id}")

        req_body = ResponseSerializers(data=request.data)
        if not req_body.is_valid():
            return failure_response(
                message="Validation Errors",
                data=req_body.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        valid_data = req_body.validated_data

        invitation_id = valid_data.get('invitation_id')
        if not invitation_id:
            return failure_response(
                message="Invitation ID is required",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        child_ref = ref.child(invitation_id)
        child_ref.delete()

        return success_response(
            message="Invitation declined successfully"
        )

    except Exception as e:
        return failure_response(
            message="An unexpected error occurred",
            data=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
