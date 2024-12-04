import django
import django_filters
from rest_framework import serializers
from app.models import User


class UserSerializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class AllUserSerializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_staff',
            'date_joined',
            'updated_at',
            'is_deleted',
            'deleted_at'
        ]

class AllUserFilterSerializers(django_filters.FilterSet):
    username = django_filters.CharFilter(field_name='username', lookup_expr='icontains')
    first_name = django_filters.CharFilter(field_name='first_name', lookup_expr='icontains')
    last_name = django_filters.CharFilter(field_name='last_name', lookup_expr='icontains')
    email = django_filters.CharFilter(field_name='email', lookup_expr='icontains')
    is_staff = django_filters.BooleanFilter(field_name='is_staff')
    is_deleted = django_filters.BooleanFilter(field_name='is_deleted')
    date_joined_start = django_filters.DateTimeFilter(field_name='date_joined', lookup_expr='gte')
    date_joined_end = django_filters.DateTimeFilter(field_name='date_joined', lookup_expr='lte')
    updated_at_start = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_at_end = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    deleted_at_start = django_filters.DateTimeFilter(field_name='deleted_at', lookup_expr='gte')
    deleted_at_end = django_filters.DateTimeFilter(field_name='deleted_at', lookup_expr='lte')
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_staff',
            'date_joined',
            'updated_at',
            'is_deleted',
            'deleted_at'
        ]

class UpdateUserSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    is_staff = serializers.BooleanField()

    class Meta:
        model = User
