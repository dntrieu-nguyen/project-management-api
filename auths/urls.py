from django.urls import path, include
from .views import *

urlpatterns = [
    path('login', login),  # POST
    path('register', register),  # POST
    path('me', profile_view, name='get_update_profile'),  # PATCH / GET
    path('password', change_password),  # PATCH
    path('refresh_token', refresh_token),
    path('forgot_password', forgot_password),
    path('reset_password', reset_password),
]
