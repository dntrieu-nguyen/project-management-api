from app.models import Project, ProjectDocument, User
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email"]

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name']

class ProjectDocumentSerializer(serializers.ModelSerializer):
    project_id = ProjectSerializer()
    owner = UserSerializer()
    class Meta:
        model = ProjectDocument
        fields = [
            'id', 
            'project_id', 
            'owner',
            'content', 
            'description',
            'name',
            'created_at', 
            'updated_at'
        ]

# validate serializers

class CreateProjectDocumentSerializer(serializers.Serializer):
    project_id = serializers.CharField(required=True)
    content = serializers.CharField(required=True)
    name = serializers.CharField(required = True)
    description = serializers.CharField()

