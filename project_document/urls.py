from django.urls import path
from .views import create_document, get_all_document

urlpatterns = [
    path('create', create_document),
    path('all', get_all_document),
    # path('all', get_all_projects_by_admin),
]
