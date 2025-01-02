from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Count
from rest_framework import status
from app.serializers import ListUserTaskSerializer
from middlewares import auth_middleware
from user.serializers import ListUserSerializer
from utils.response import failure_response, success_response

from .models import Task, Project


@api_view(['GET'])
@auth_middleware
def get_statistics(request):
    try:
        # Lấy thống kê cho Project theo status
        project_stats = (
            Project.objects.values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        )

        # Lấy thống kê cho Task theo status
        task_stats = (
            Task.objects.values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        )

        # Tạo response data
        return success_response(
            data= {
                "project": project_stats,
                "task": task_stats
            }
        )
    except Exception as e:
      return failure_response(
            message=str(e),
            data=None,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
      )

@api_view(['POST'])
@auth_middleware
def get_list_user_project(request):
    try:
        req_body = ListUserTaskSerializer(data=request.data)
        if not req_body.is_valid():
            return failure_response(
                message="Validation errors",
                data=req_body.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        project_id = req_body.validated_data['project_id']
        project = Project.objects.get(id=project_id)

        # Lấy danh sách user trong project
        users = [project.owner] + list(project.members.filter(is_deleted=False)) if project.owner else list(project.members.filter(is_deleted=False))

        # owner của project
        users_data = ListUserSerializer(users, many=True).data


        return success_response(
            data=users_data
        )
    except Exception as e:
        return failure_response(
            message="An unexpected error occurred",
            data=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
