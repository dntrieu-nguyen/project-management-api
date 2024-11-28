from django.urls import path

from notifications.views import get_all_notifications_by_user, send_notifications_to_user, update_status_notifications


urlpatterns = [
    path('all', get_all_notifications_by_user),
    path('create', send_notifications_to_user),
    path('update-status', update_status_notifications),
]
