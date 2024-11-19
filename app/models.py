import datetime
from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class SoftDeleteMixin(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = models.Manager()  
    all_objects = models.Manager()  

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, soft=True):
        """
        Soft delete by default; use soft=False for hard delete.
        """
        if soft:
            self.is_deleted = True
            self.deleted_at = datetime.datetime.now()
            self.save()
        else:
            super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """
        Restore a soft-deleted object.
        """
        self.is_deleted = False
        self.deleted_at = None
        self.save()



class User(AbstractUser, SoftDeleteMixin):
    # Extend AbstractUser with additional fields for password reset
    forget_password_token = models.CharField(max_length=255, blank=True, null=True)
    forget_password_expires_at = models.DateTimeField(blank=True, null=True)

    reset_password_token = models.CharField(max_length=255, blank=True, null=True)
    reset_password_expires_at = models.DateTimeField(blank=True, null=True)


class Project(SoftDeleteMixin):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="owned_projects", blank=True, null=True)
    members = models.ManyToManyField(User, related_name="projects")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Task(SoftDeleteMixin):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, default='pending')  # pending, completed, in-progress
    priority = models.IntegerField(default=1)  # 1 (low), 2 (medium), 3 (high)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, blank=True, null=True, related_name="tasks")
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks")
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Comment(SoftDeleteMixin):
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="comments")
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, blank=True, null=True, related_name="comments")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.task.title}"


class Message(SoftDeleteMixin):
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="sent_messages")
    receiver = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="received_messages")
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username}"


class Notification(SoftDeleteMixin):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="notifications")
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"


class RefreshToken(SoftDeleteMixin):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="refresh_token")
    token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"RefreshToken for {self.user.username}"