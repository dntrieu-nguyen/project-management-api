from uuid import UUID
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework import status
from django.db.models import Q
from app.models import Project, ProjectDocument, User
from middlewares import auth_middleware
from project_document.serializers import CreateProjectDocumentSerializer, ProjectDocumentSerializer
from utils.pagination import Pagination
from utils.response import failure_response, success_response

# Create your views here.


@api_view(["POST"])
@auth_middleware
def create_document(request):
    try:
        user_id = str(request.user['id'])
        req_body = CreateProjectDocumentSerializer(data=request.data)

        if not req_body.is_valid():
            return failure_response(
                message="Validation Error",
                data= req_body.errors
            )
        valid_data = req_body.validated_data

        owner = User.objects.filter(id = UUID(user_id)).first()

        project = Project.objects.filter(
            Q(id = UUID(valid_data['project_id'])) &
            (Q(owner = UUID(user_id)) | 
            Q(members__id = UUID(user_id)))
        )

        if not project.exists():
            return failure_response(
                message="You dont have permission for this action"
            )
        
        ProjectDocument.objects.create(
            project_id= project.first(),
            owner = owner,
            content = valid_data["content"],
            description = valid_data['description'],
            name = valid_data['name']
        )

        
        
        return success_response(
            message="create successfully",
            data = valid_data
        )
        
    except Exception as e:
       return failure_response(
            message="An unexpected error occurred",
            data=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
@api_view(["GET"])
@auth_middleware
def get_all_document(request):
    try:
        user_id = request.user['id']

        query_set = ProjectDocument.objects.filter(
            owner = user_id
        )

        paginator = Pagination()
        paginated_document = paginator.paginate_queryset(query_set,request)

        data = ProjectDocumentSerializer(paginated_document, many=True).data
        return success_response(
            paginator = paginator,
            data=data
        )
      
    except Exception as e:
       return failure_response(
            message="An unexpected error occurred",
            data=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )