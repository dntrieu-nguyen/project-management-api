from django.urls import path
from .views import accept_invite, add_user_to_project, create_project, decline_invite, delete_project_by_owner_or_admin, delete_user_from_project, get_all_projects_by_admin, get_list_project, get_project_by_filter, restore_project, update_project

urlpatterns = [
    path('create', create_project),
    path('all', get_all_projects_by_admin),
    path('filter', get_project_by_filter),
    path('add-user', add_user_to_project),
    path('delete-user', delete_user_from_project),
    path('delete', delete_project_by_owner_or_admin),
    path('restore', restore_project),
    path('list', get_list_project),
    path('accept-invite',accept_invite),
    path('decline-invite', decline_invite),
    path('update', update_project),
]
