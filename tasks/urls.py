from django.urls import path
from .views import *

urlpatterns = [
    path('<int:id>', get_task_by_id),
    path('', get_tasks_by_project_id),
    path('create', create_task),
    path('update/<int:task_id>', update_task),
    path('delete/<int:task_id>', delete_task),
]
