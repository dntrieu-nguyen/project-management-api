from django.urls import path

from notifications.views import get_all_notifications_by_user, seen_notification_by_user, send_notifications_to_user


urlpatterns = [
    path('all', get_all_notifications_by_user),
    path('create', send_notifications_to_user),
    path('update-status', seen_notification_by_user),
]
