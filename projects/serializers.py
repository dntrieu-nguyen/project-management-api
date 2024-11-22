from app.models import Project
from rest_framework import serializers
import django_filters

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
            'updated_at_end']