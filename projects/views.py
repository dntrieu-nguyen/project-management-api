from datetime import datetime
import json
import pytz
from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from app.models import Project, User
from middlewares import auth_middleware
from projects.serializers import AddOrDeleteUserToProjectSerializers, CreateProjectSerializers, DeleteProjectErrorResponseSerializer, DeleteProjectSuccessResponseSerializer, ListProjectSerializer, ProjectFilter, ProjectSerializer, RequireBody, RestoreProjectErrorResponseSerializer, RestoreProjectSuccessResponseSerializer
from utils.pagination import Pagination
from utils.response import failure_response, success_response
from uuid import UUID
from django.db.models import Q
from drf_yasg import openapi
from firebase.firebase_config import db
# Create new project
@swagger_auto_schema(
    method='POST',
    operation_description="Create a project",
    tags=["Projects"],
    request_body=CreateProjectSerializers,
    security=[{'Bearer': []}]
)
@api_view(['POST'])
@auth_middleware
def create_project(request):
    """
    API Create a new project
    """
    try:
        user_id = request.user['id']
        serializer = CreateProjectSerializers(data=request.data)
        

    
        # Check validate
        if not serializer.is_valid():
            return failure_response(
                message="Validation Errors",
                data=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        validated_data = serializer.validated_data

        # Get owner
        try:
            owner = User.objects.get(id=request.user['id'])
        except User.DoesNotExist:
            return failure_response(
                message="Owner does not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check unique project name
        if Project.objects.filter(name=validated_data['name'], owner=owner).exists():
            return failure_response(
                message="This project name already exists",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Get list of members (members is a string of comma-separated UUIDs)
        members_string = validated_data.get('members', '')
        member_ids = members_string.split(',') if members_string else []

        # case member has user id:
        if bool(members_string):
            # Check if member IDs are unique
            if len(member_ids) != len(set(member_ids)):
                return failure_response(
                    message="Duplicate members found",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            # Get members from the database
            members = User.objects.filter(id__in=member_ids)
            
            # Check if all members exist (including owner)
            if len(members) != len(member_ids):
                return failure_response(
                    message="One or more members do not exist",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        # Create project
        project = Project.objects.create(
            name=validated_data['name'],
            description=validated_data.get('description', ''),
            owner=owner,
            start_date = validated_data['start_date'],
            end_date = validated_data['end_date'],
            status = validated_data['status']
        )

        if bool(members_string):
            # Add members to project (including owner)
            for user in member_ids:
                new_data = {
                    "project": str(project.id),
                    "status": "pending",
                    "from": owner.email,
                    "type":"invite",
                    "context":"project",
                    "message": f"You have a invitation to join project {project.name} from {owner.email}",
                    "created_at" : datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                }
                ref = db.reference(f"invitedNotifications/{user}")
                ref.push(new_data)

        # Serialize the project data
        project_data = ProjectSerializer(project).data

        return success_response(
            message="Create project successfully",
            status_code=status.HTTP_201_CREATED,
            data=project_data
        )
    except Exception as e:
      return failure_response(
            message="An unexpected error occurred",
            data=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Get all project by admin
@swagger_auto_schema(
    method='GET',
    operation_description="Get all projects by admin",
    tags=["Projects"],
    security=[{'Bearer': []}]
)
@api_view(['GET'])
@auth_middleware
def get_all_projects_by_admin(request):
    current_user = request.user
    if not current_user['role']: 
        return failure_response(
            message="You dont have permission for this action",
            status_code= status.HTTP_403_FORBIDDEN
            )
    query_set = Project.objects.all()

    # Filter
    project_filter = ProjectFilter(request.GET, queryset=query_set)  
    filtered_projects = project_filter.qs

    # paginate
    paginator = Pagination()
    paginated_projects = paginator.paginate_queryset(filtered_projects, request)

    # serializer data
    data = ProjectSerializer(paginated_projects, many=True).data
    return success_response(
        message="Operator successfull",
        data= data, 
        paginator=paginator
        )

# Get project with filter
@swagger_auto_schema(
    method='GET',
    operation_description="Get project with filter by owner",
    tags=["Projects"],
    security=[{'Bearer': []}]
)
@api_view(['GET'])
@auth_middleware
def get_project_by_filter(request):
    current_user = request.user
    
    # get all project of user
    query_set = Project.objects.filter(
        (Q(owner=UUID(current_user['id'])) | 
        Q(members__id=UUID(current_user['id'])))
        & Q(is_deleted = False)
        ).distinct() 

    # apply filter
    project_filter = ProjectFilter(request.GET, queryset=query_set)  
    filtered_projects = project_filter.qs

    # paginate
    paginator = Pagination()
    paginated_projects = paginator.paginate_queryset(filtered_projects, request)

    # serializer data
    data = ProjectSerializer(paginated_projects, many=True).data

    return success_response(
        message="Operator successfully",
        data= data, 
        paginator=paginator
        )

@swagger_auto_schema(
    method='POST',
    operation_description="Add user to project",
    tags=["Projects"],
    request_body=AddOrDeleteUserToProjectSerializers,
    security=[{'Bearer': []}]
)
@api_view(['POST'])
@auth_middleware
def add_user_to_project(request):
    try:
        user_id = str(request.user['id'])
        req_body = AddOrDeleteUserToProjectSerializers(data=request.data)

        if not req_body.is_valid():
            return failure_response(
                message="Validation Errors",
                data=req_body.errors
            )

        validated_data = req_body.validated_data
        req_members_list = json.loads(validated_data['members']) 
        if not req_members_list:
            return failure_response(
                message="Members are required"
            )

        project = Project.objects.filter(
            Q(owner=user_id) & Q(id=validated_data['project_id'])
        ).first()

        if not project:
            return failure_response(message="You are not the owner of this project", status_code=status.HTTP_403_FORBIDDEN)

        current_member_ids = {str(member.id) for member in project.members.all()}

        new_members = []
        invalid_members = []
        exist_members = []
        for member_id in req_members_list:
            try:
                member = User.objects.get(id=member_id)
                if member_id not in current_member_ids:
                    project.members.add(member)
                    new_members.append(str(member.id))
                else:
                   exist_members.append(member_id)
            except User.DoesNotExist:
                invalid_members.append(member_id)

        if invalid_members:
            return failure_response(
                message="Some users were not found",
                data={
                    "invalid_members":invalid_members
                },
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if exist_members:
            return failure_response(
                message="Some users have been member already",
                data={
                    "exist_members": exist_members
                }
            )
        
        return success_response(
            message="Users added successfully",
            data={"added_members": new_members}
        )

    except Exception as e:
        return failure_response(
            message="An unexpected error occurred",
            data=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    


#delete member from user
@swagger_auto_schema(
    method='DELETE',
    operation_description="Delete user from project",
    request_body=AddOrDeleteUserToProjectSerializers,
    tags=["Projects"],
    security=[{'Bearer': []}]
)
@api_view(['DELETE'])
@auth_middleware
def delete_user_from_project(request):
    try:
        user_id = str(request.user['id'])
        req_body = AddOrDeleteUserToProjectSerializers(data=request.data)
        if not req_body.is_valid():
            return failure_response(
                message="Validation Errors",
                data= req_body.errors
            )
        validated_data = req_body.validated_data
        req_members_list = json.loads(validated_data['members']) 
        if not req_members_list:
            return failure_response(
                message="Members are required"
            )
        project = Project.objects.filter(
            Q(owner=user_id) & Q(id=validated_data['project_id'])
        ).first()

        if not project:
            return failure_response(message="You are not the owner of this project", status_code=status.HTTP_403_FORBIDDEN)

        current_member_ids = {str(member.id) for member in project.members.all()}

        removed_members = []
        not_member = []
        for member_id in req_members_list:
            try:
                member = User.objects.get(id=member_id)
                if member_id in current_member_ids:
                    project.members.remove(member)  
                    removed_members.append(str(member.id))
                else:
                    not_member.append(member_id)
            except User.DoesNotExist:
                not_member.append(member_id)

        if not_member:
            return failure_response(
                message="Some users were not found in this project",
                data={"not_member": not_member},
                status_code=status.HTTP_404_NOT_FOUND
            )

        return success_response(
            message="Users removed successfully",
            data={"removed_members": removed_members}
        )
    except Exception as e:
        return failure_response(
            message="An unexpected error occurred",
            data=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
# delete projects
@swagger_auto_schema(
    method='DELETE',
    operation_description="Delete a project by owner or admin",
    tags=["Projects"],
    security=[{'Bearer': []}],
    manual_parameters=[
        openapi.Parameter(
            'project_id',
            openapi.IN_QUERY,
            description="ID của dự án cần xoá",
            type=openapi.TYPE_STRING,
            required=True
        ),
    ],
    responses={
        200: DeleteProjectSuccessResponseSerializer,
        400: DeleteProjectErrorResponseSerializer,
        406: "You have no permission for this action",
        500: "An unexpected error occurred"
    }
)
@api_view(['DELETE'])
@auth_middleware
def delete_project_by_owner_or_admin(request):
    try:
        user = request.user
        project_id = request.query_params['project_id']

        if not bool(project_id):
            return failure_response(
                message="Validation Errors",
                data= {
                    "project_id": "project_id is required"
                }
            )
        
        project = Project.objects.filter( Q(owner=user['id']) & Q(id=project_id)).first()

        if user['role'] or project:
            """
            Trong project có task chưa hoàn thành thì không xoá
            """
            current_tasks = project.tasks.all()

            task_not_completed = []
            now_utc = datetime.utcnow().replace(tzinfo=pytz.UTC)

            for task in current_tasks:
                if task.due_date:  #
                    if isinstance(task.due_date, datetime):
                        due_date = task.due_date
                    else:
                        
                        due_date = datetime.strptime(task.due_date, "%Y-%m-%dT%H:%M:%S%z")

                    if due_date > now_utc: 
                        task_not_completed.append(task.id)

            if bool(len(task_not_completed)):
                return failure_response(
                    message="Complete all tasks before deleting the project",
                    data={"incomplete_tasks": task_not_completed}
                )
            project.delete(soft=True)
            return success_response(
            message="Delete project successfully",
            data={
                "project": project_id
            }
        )
        return failure_response(
                message="You have no permission for this action",
                status_code=status.HTTP_406_NOT_ACCEPTABLE
            )

    except Exception as e:
        return failure_response(
            message="An unexpected error occurred",
            data=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# restore project
@swagger_auto_schema(
    method='POST',
    operation_description="Restore project",
    tags=["Projects"],
    security=[{'Bearer': []}],
    manual_parameters=[
        openapi.Parameter(
            'project_id',
            openapi.IN_QUERY,
            description="ID của dự án cần khôi phục",
            type=openapi.TYPE_STRING,
            required=True
        ),
    ],
    responses={
        200: RestoreProjectSuccessResponseSerializer,
        400: RestoreProjectErrorResponseSerializer,
        403: "You don't have permissions for this action",
        500: "An unexpected error occurred",
    }
)
@api_view(['POST'])
@auth_middleware
def restore_project(request):
    try:
        user = request.user
        project_id = request.query_params['project_id']
        
        if not bool(project_id):
            return failure_response(
                message="Validation Errors",
                data= {
                    "project_id": "project_id is required"
                }
            )
        
        project = Project.objects.filter( Q(owner=user['id']) & Q(id=project_id)).first()
        
        if not user['role']:
            return failure_response(
                message="You dont have permissions for this action",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        project.restore()

        return success_response(
            message="restore successfully"
        )
    except Exception as e:
        return failure_response(
            message="An unexpected error occurred",
            data=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@auth_middleware
def get_list_project(request):
    try:
      user_id = request.user['id']
      query_set = Project.objects.filter(
          (Q( owner = user_id) | Q(members__id = user_id))
        ).distinct()
      paginator = Pagination()
      paginated_project = paginator.paginate_queryset(query_set, request)

      data = ListProjectSerializer(paginated_project, many=True).data
      return success_response(
          paginator = paginator,
          data = data
      )
      
    except Exception as e:
      return failure_response(
            message="An unexpected error occurred",
            data=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@auth_middleware
def accept_invite(request):
    try:
      user_id = request.user['id']
      req_body = RequireBody(data=request.data)

      if not req_body.is_valid():
        return failure_response(
            message="Validation erros",
            data= req_body.errors
        )
      
      valid_data = req_body.validated_data

      project = Project.objects.filter(id=valid_data['project_id']).first()
      user = User.objects.filter(id = user_id).first()

      if not project:
          return failure_response(
              message="Project not found",
              status_code= status.HTTP_404_NOT_FOUND
          )
      
      if project.members.filter(id = user_id).exists():
          return failure_response(
              message="User is already a member of this project"
          )
      # add members to projects
      project.members.add(user)

      ref = db.reference(f"invitedNotifications/{user_id}")
      notification = ref.child(valid_data['notification_id'])

      member_ids = project.members.exclude(id=user_id)

      for member in member_ids:
          ref_member = db.reference(f"notifications/{str(member)}")
          new_notification = {
            "title": f"{project.name}",
            "content" : f"{user.email} has joined {project.name}",
            "is_read": False,
            "sender_id": user_id,
            "created_at": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            "updated_at":datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        }
          ref_member.push(new_notification)

      #delete notification
      notification.delete()

      ref_owner = db.reference(f"notifications/{str(project.owner.id)}")
      new_notification = {
            "title": f"{project.name}",
            "content" : f"{user.email} has accept your invitation",
            "is_read": False,
            "sender_id":user_id,
            "created_at": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            "updated_at":datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        }
      ref_owner.push(new_notification)

      return success_response(
        message=f"User {user.email} has been successfully added to project {project.name}.",
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
def decline_invite(request):
    try:
        # Retrieve user ID from the authenticated request
        user_id = request.user['id']
        req_body = RequireBody(data=request.data)

        # Validate request body
        if not req_body.is_valid():
            return failure_response(
                message="Validation errors",
                data=req_body.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Extract validated data
        valid_data = req_body.validated_data

        user = User.objects.get(id=user_id)

        # Check if the project exists
        project = Project.objects.filter(id=valid_data['project_id']).first()
        if not project:
            return failure_response(
                message="Project not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Check if the notification exists in Firebase
        ref = db.reference(f"invitedNotifications/{user_id}")
        notification = ref.child(valid_data['notification_id'])
        if not notification.get():
            return failure_response(
                message="Notification not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Delete the notification to decline the invite
        notification.delete()

        # Send notification to owner
        ref_owner = db.reference(f"notifications/{str(project.owner.id)}")

        new_notification = {
            "title": f"{project.name}",
            "content" : f"{user.email} has decline you invitation",
            "is_read": False,
            "sender_id":user_id,
            "created_at": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            "updated_at":datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        }

        ref_owner.push(new_notification)

        return success_response(
            message=f"Invitation to join project {project.name} has been declined.",
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        # Handle unexpected errors and return a failure response
        return failure_response(
            message="An unexpected error occurred",
            data=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['PATCH'])
@auth_middleware
def update_project(request):
    try:
        user_id = request.user['id']
        
       
        req_body = CreateProjectSerializers(data=request.data)

        if not req_body.is_valid():
            return failure_response(
                message="Validation errors",
                data=req_body.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        validated_data = req_body.validated_data

        project = Project.objects.filter(
            Q(owner=user_id) & Q(id=validated_data['project_id'])
        ).first()

        if not project:
            return failure_response(
                message="Project not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        if project.owner != user_id:
            return failure_response(
                message="You are not the owner of this project",
                status_code=status.HTTP_403_FORBIDDEN
            )

        project.name = validated_data['name']
        project.description = validated_data.get('description', '')
        project.start_date = validated_data['start_date']
        project.end_date = validated_data['end_date']
        project.status = validated_data['status']
        project.updated_at = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        # add members to projects
        members_string = validated_data.get('members', '')
        member_ids = members_string.split(',') if members_string else []

        if bool(members_string):
            for user in member_ids:
                # if user not in members project or user not is owner, send invitation
                if user not in project.members or user != project.owner:
                    new_data = {
                        "project": str(project.id),
                        "status": "pending",
                        "from": project.owner.email,
                        "type":"invite",
                        "context":"project",
                        "message": f"You have a invitation to join project {project.name} from {project.owner.email}",
                        "created_at" : datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                    }
                    ref = db.reference(f"invitedNotifications/{user}")
                    ref.push(new_data)
            
        project.save()

        return success_response(
            message="Project updated successfully",
            data=ProjectSerializer(project).data
        )
    except Exception as e:
        return failure_response(
                message="An unexpected error occurred",
                data=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )