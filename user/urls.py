from django.urls import path

from user.views import delete_user_by_admin, get_all_user_by_admin, get_list_user, restore_user_by_admin

urlpatterns = [
    path('all', get_all_user_by_admin),
    path('delete', delete_user_by_admin),
    path('restore', restore_user_by_admin),
    path('list', get_list_user)
]
