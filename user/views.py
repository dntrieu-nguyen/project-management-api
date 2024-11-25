from uuid import UUID
from rest_framework import status
from rest_framework.decorators import api_view
from app.models import User
from middlewares import auth_middleware
from drf_yasg.utils import swagger_auto_schema
from user.serializers import AllUserFilterSerializers, AllUserSerializers, UpdateUserSerializer
from utils.pagination import Pagination
from utils.response import failure_response, success_response


# Create your views here.

# get all user by admin
@swagger_auto_schema(
    method='GET',
    operation_description="Get all users by admin",
    tags=["Users"],
    security=[]
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

