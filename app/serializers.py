
import django_filters
from rest_framework import serializers

from app.models import Project, User


class ListUserTaskSerializer(serializers.Serializer):
    project_id = serializers.CharField(required=True)
    
    
class ListUserProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'avatar']