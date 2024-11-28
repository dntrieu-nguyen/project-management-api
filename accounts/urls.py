
from django.urls import path
from accounts.views import  test_view 

urlpatterns = [
    # path('login/', AccountsView.as_view(), name='login'),
    path('test/', test_view, name='test'),
]
