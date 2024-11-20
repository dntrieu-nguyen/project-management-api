from django.urls import path, include
from .views import *

urlpatterns = [
    path('login/', login),  # POST
    path('register/', register),  # POST
    path('me/', profile_view, name='update_profile'),  # PATCH
    path('password/', change_password),  # PATCH
]
