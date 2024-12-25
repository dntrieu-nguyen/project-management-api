from uuid import UUID
from rest_framework import status
from rest_framework.decorators import api_view
from django.db.models import Q
from app.models import Project, User
from middlewares import auth_middleware
from drf_yasg.utils import swagger_auto_schema
from user.serializers import AllUserFilterSerializers, AllUserSerializers, ListUserInProjectSerializers, UpdateUserSerializer
from utils.pagination import Pagination
from utils.response import failure_response, success_response


# Create your views here.

# get all user by admin
@swagger_auto_schema(
    method='GET',
    operation_description="Get all users by admin",
    tags=["Users"],
    security=[{'Bearer': []}]
)
@api_view(['GET'])
@auth_middleware
def get_all_user_by_admin(request):
    # check role
    current_user = request.user
    if not current_user['role']: 
        return failure_response(
            message='You dont have permission for this action',
            status_code= status.HTTP_403_FORBIDDEN
            )
    
    # query set
    query_set = User.objects.all()

    # apply filter
    user_filter = AllUserFilterSerializers(request.GET, queryset=query_set)  
    filtered_users = user_filter.qs

    # paginate
    paginator = Pagination()
    paginated_projects = paginator.paginate_queryset(filtered_users, request)

    # serializing data
    data = AllUserSerializers(paginated_projects, many=True).data
    return success_response(data=data, paginator=paginator)

# block user by admin
@swagger_auto_schema(
    method='PUT',
    operation_description="delete users by admin",
    tags=["Users"],
    security=[{'Bearer': []}]
)
@api_view(['PUT'])
@auth_middleware
def delete_user_by_admin(request):
    current_user = request.user
    id = request.query_params.get('id')
   
    if not current_user['role']:
        return failure_response(
            status_code=status.HTTP_403_FORBIDDEN,
            message="you dont have permissions for this action")
    
    if not bool(id):
        return failure_response(message='missing user id')

 
    # # get user by id
    user = User.objects.filter(id = UUID(id)).first()

    if not user:
        return failure_response(message="user not found")

    # # soft delete user
    user.delete(soft=True)

    return success_response(message='deleted successfully')


@swagger_auto_schema(
    method='POST',
    operation_description="Restore users by admin",
    tags=["Users"],
    security=[{'Bearer': []}]
)
@api_view(['POST'])
@auth_middleware
def restore_user_by_admin(request):
    try:
        current_user = request.user
        user_id = request.query_params.get("user_id")
        # check valid user_id
        if not bool(user_id):
            return failure_response(
                message="Validtions Errors",
                data={
                    "user_id":"This field is required"
                }
            )
        # check user permission
        if not current_user["role"]:
            return failure_response(
                message="You dont have permission for this action"
            )
        
        user = User.objects.filter(id = UUID(user_id)).first()
        # check existance user
        if not user:
            return failure_response(
                message="User not found",
                status_code= status.HTTP_403_FORBIDDEN
            )
        # restore user
        user.restore()
        
        return success_response(
            message="restore user successfully",
            data= {
                "user_restored":user_id
            }
        )
    except Exception as e:
         return failure_response(
            message="An unexpected error occurred",
            data=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@auth_middleware
def get_list_user(request):
    try:
        user_id = request.user['id']
        req_body = ListUserInProjectSerializers(data=request.data)
        if not req_body.is_valid():
            return failure_response(
                message="Validation Error",
                data= req_body.errors
            )
        valid_data = req_body.validated_data
        project = Project.objects.filter(
            Q(id = UUID(valid_data['project_id'])) &
            (Q(owner = UUID(user_id)) | 
            Q(members__id = UUID(user_id)))
        )
        
        # get all user in project id
        users = project.first().members.all()
        # owner = project.first().owner
        # get all user in project
        data = {
            # "owner": owner.email,
            "members": ListUserInProjectSerializers(users, many=True).data
        }
        
        return success_response(
            message="get list user successfully",
            data = data
        )
    except Exception as e:
      return failure_response(
            message="An unexpected error occurred",
            data=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR   
      )