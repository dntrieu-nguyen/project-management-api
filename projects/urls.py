from django.urls import path
from .views import create_project, get_all_projects_by_admin, get_project_by_filter

urlpatterns = [
    path('create/', create_project),
    path('all/', get_all_projects_by_admin),
    path('filter/', get_project_by_filter)
]
