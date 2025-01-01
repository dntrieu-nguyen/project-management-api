import priority
from rest_framework import serializers
import datetime
from app.models import Task, Project, User
from rest_framework.serializers import ModelSerializer


class GetTasksSerializer(serializers.Serializer):
    page = serializers.IntegerField(
        required=False, default=1, min_value=1, help_text="Page number for pagination")
    per_page = serializers.IntegerField(
        required=False, default=10, min_value=1, help_text="Number of items per page")
    project_id = serializers.CharField(
        min_length=5,
        help_text="Project id"
    )


class CreateTaskSerializer(serializers.Serializer):
    title = serializers.CharField(
        required=True,
        min_length=5,
        max_length=30
    )
    description = serializers.CharField(
        required=True,
        min_length=5,
        max_length=200,
    )
    due_date = serializers.DateTimeField(
        required=True,
    )
    project_id = serializers.UUIDField(required=True)
    assignees = serializers.ListField(
        child=serializers.UUIDField(),  # Đảm bảo mỗi phần tử trong mảng là UUID hợp lệ
        required=False,
    )
    status = serializers.CharField(
        required=True,
    )
    start_date = serializers.DateTimeField(
        required=True,
    )
    end_date = serializers.DateTimeField(
        required=True,
    )
    estimate_hour = serializers.FloatField()
    actual_hour = serializers.FloatField()
    priority = serializers.IntegerField()

class UpdateTaskSerializer(serializers.Serializer):
    title = serializers.CharField(
        required=False,
        min_length=5,
        max_length=30
    )
    description = serializers.CharField(
        required=False,
        min_length=5,
        max_length=200,
    )
    due_date = serializers.DateTimeField(
        required=False,
    )
    task_id = serializers.UUIDField(required=True)
    project_id = serializers.UUIDField(required=True)
    assignees = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )   
    status = serializers.CharField(
        required=False,
    )
    estimate_hour = serializers.FloatField(
        min_value=0
    )
    actual_hour = serializers.FloatField(
        min_value=0
    )
    def validate_status(self, value):

        valid_values = ["pending" , "in-process" , "completed" , "open" , "close" , "cancel"]
        if (value not in valid_values ):
            raise serializers.ValidationError(
                "Status must be pending or completed")
        return value

    def validate_members(self, value):
        unique_members = list(set(value))
        return unique_members


class AssigneeSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email',
                  'is_staff', 'is_active', 'date_joined', 'updated_at']
        read_only_fields = ['id']


class TaskSerializer(ModelSerializer):
    assignees = AssigneeSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'created_at',
                  'updated_at', 'is_deleted', 'status', 'priority', 
                  'due_date', 'assignees', 'start_date', 'end_date', 'estimate_hour','actual_hour']
        
        read_only_fields = ['id']


class ProjectSerializer(ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'tasks']

class SendNotificationSerializers(serializers.Serializer):
    receiver_id = serializers.CharField()
    task_id = serializers.CharField()
    project_id = serializers.CharField()

class ResponseSerializers(serializers.Serializer):
    notification_id = serializers.CharField()
    task_id = serializers.CharField()
