
from django.urls import path

from comments.views import create_comment_task_by_user, create_reply_comment_by_user, delete_comment_by_user, delete_reply_comment_by_user, update_comment_by_user, update_reply_comment_by_user


urlpatterns = [
    path('create', create_comment_task_by_user),
    path('update', update_comment_by_user),
    path('delete', delete_comment_by_user),
    path('create-reply-comment', create_reply_comment_by_user),
    path('update-reply-comment', update_reply_comment_by_user),
    path('delete-reply-comment', delete_reply_comment_by_user),

]
