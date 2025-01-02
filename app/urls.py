
from django.urls import path

from app.views import get_list_user_project, get_statistics


urlpatterns = [
    path('get-statistics', get_statistics),
    path('get-list-user-project', get_list_user_project),
]
