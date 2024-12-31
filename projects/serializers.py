from app.models import Project, ProjectDocument, Task, User
from rest_framework import serializers
import django_filters
from django.db.models import Q

class CreateProjectSerializers(serializers.Serializer):
    name = serializers.CharField(
        required=True, 
        max_length=50, 
        min_length=3
    )
    description = serializers.CharField(
        required=False, 
        max_length=300,
        allow_blank=True  
    )
    members = serializers.CharField(required=False)
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    status = serializers.CharField()
    def validate(self, data):
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                "end_date": "End date must be later than start date."
            })

        return data

class RequireBody(serializers.Serializer):
    notification_id = serializers.CharField()
    project_id = serializers.CharField()

class UpdateProjectSerializers(serializers.Serializer):
    name = serializers.CharField(
        required=True, 
        max_length=50, 
        min_length=3
    )
    description = serializers.CharField(
        required=False, 
        max_length=300,
        allow_blank=True  
    )
    members = serializers.CharField(required=False)
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    def validate(self, data):
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                "end_date": "End date must be later than start date."
            })

        return data


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'

class ProjectFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    status = django_filters.ChoiceFilter(field_name='status', choices=Project.STATUS_CHOICES)
    owner = django_filters.UUIDFilter(field_name='owner__id')
    member = django_filters.UUIDFilter(field_name='members__id')
    created_at_start = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_end = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    updated_at_start = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_at_end = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    start_date_start = django_filters.DateTimeFilter(field_name='start_date', lookup_expr='gte')
    start_date_end = django_filters.DateTimeFilter(field_name='start_date', lookup_expr='lte')
    end_date_start = django_filters.DateTimeFilter(field_name='end_date', lookup_expr='gte')
    end_date_end = django_filters.DateTimeFilter(field_name='end_date', lookup_expr='lte')

    class Meta:
        model = Project
        fields = [
            'name', 
            'status', 
            'owner', 
            'member', 
            'created_at_start', 
            'created_at_end', 
            'updated_at_start', 
            'updated_at_end',
            'start_date_start',
            'start_date_end',
            'end_date_start',
            'end_date_end',
            ]

class AddOrDeleteUserToProjectSerializers(serializers.Serializer):
    project_id = serializers.CharField()
    members = serializers.CharField()


class ListUserInProjectSerializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email']

class ListTaskInProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'is_deleted']

class ListDocumentInProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectDocument
        fields = ['id', 'name', 'is_deleted']

class ListProjectSerializer(serializers.ModelSerializer):
    tasks = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'name', 'tasks', 'documents']

    def get_tasks(self, obj):
        tasks = Task.objects.filter(project_id=obj.id)
        return ListTaskInProjectSerializer(tasks, many=True).data

    def get_documents(self, obj):
        documents = ProjectDocument.objects.filter(project_id=obj.id)
        return ListDocumentInProjectSerializer(documents, many=True).data
"""
Serializers for swagger
"""

# Serializer cho phản hồi thành công
class RestoreProjectSuccessResponseSerializer(serializers.Serializer):
    message = serializers.CharField(default="restore successfully")

# Serializer cho lỗi
class RestoreProjectErrorResponseSerializer(serializers.Serializer):
    message = serializers.CharField(default="Validation Errors")
    data = serializers.DictField(
        child=serializers.CharField(),
        default={"project_id": "project_id is required"}
    )


# Serializer cho phản hồi thành công
class DeleteProjectSuccessResponseSerializer(serializers.Serializer):
    message = serializers.CharField(default="Delete project successfully")
    data = serializers.DictField(
        child=serializers.CharField(),
        default={"project": "project_id"}
    )

# Serializer cho phản hồi lỗi
class DeleteProjectErrorResponseSerializer(serializers.Serializer):
    message = serializers.CharField(default="Validation Errors")
    data = serializers.DictField(
        child=serializers.ListField(),
        default={"incomplete_tasks": [1, 2, 3]}
    )
