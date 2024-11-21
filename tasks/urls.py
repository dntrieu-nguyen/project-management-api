from django.urls import path, include
from .views import *

urlpatterns = [
    path('<int:id>', get_task_by_id),  # POST
]
