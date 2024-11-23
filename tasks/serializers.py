from rest_framework import serializers
import datetime


class GetTasksSerializer(serializers.Serializer):
    page = serializers.IntegerField(
        required=False, default=1, min_value=1, help_text="Page number for pagination")
    per_page = serializers.IntegerField(
        required=False, default=10, min_value=1, help_text="Number of items per page")
    project_id = serializers.CharField(
        min_length=5,
        max_length=20,
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
    project_id = serializers.CharField(
        required=True
    )
    members = serializers.ListField(
        child=serializers.CharField(),
        required=True,
    )
    status = serializers.CharField(
        required=True,
    )


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
    project_id = serializers.CharField(
        required=False
    )
    members = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
    status = serializers.CharField(
        required=False,
    )
