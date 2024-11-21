from rest_framework import status
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from app.models import Project, User
from middlewares import auth_middleware
from projects.serializers import CreateProjectSerializers, ProjectFilter, ProjectSerializer
from utils.pagination import Pagination
from utils.response import failure_response, success_response
from uuid import UUID
from django.db.models import Q
# Create new project
@swagger_auto_schema(
    method='POST',
    operation_description="Create a project",
    tags=["Projects"],
    request_body=CreateProjectSerializers,
    security=[]
)
@api_view(['POST'])
@auth_middleware
def create_project(request):
    """
    API Create a new project
    """
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
        owner=owner
    )

    if bool(members_string):
        # Add members to project (including owner)
        project.members.set(members)

    # Serialize the project data
    project_data = ProjectSerializer(project).data

    return success_response(
        message="Create project successfully",
        status_code=status.HTTP_201_CREATED,
        data=project_data
    )

# Get all project by admin
@swagger_auto_schema(
    method='GET',
    operation_description="Get all projects by admin",
    tags=["Projects"],
    security=[]
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
    paginator = Pagination()  
    result_page = paginator.paginate_queryset(query_set, request)
    data = ProjectSerializer(result_page, many=True).data
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
    security=[]
)
@api_view(['GET'])
@auth_middleware
def get_project_by_filter(request):
    current_user = request.user
    # get all project of user
    query_set = Project.objects.filter(
        Q(owner=UUID(current_user['id'])) | Q(members__id=UUID(current_user['id']))).distinct() 

    # apply filter
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
