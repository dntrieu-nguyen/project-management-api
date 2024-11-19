
from django.urls import path
from accounts.views import AccountsView 

urlpatterns = [
    path('login/', AccountsView.as_view(), name='login'),
]
