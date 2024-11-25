import datetime
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.
class SoftDeletedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class SoftDeleteMixin(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = SoftDeletedManager()  
    all_objects = models.Manager() 

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, soft=True):
        if soft:
            self.is_deleted = True
            self.deleted_at = datetime.datetime.now()
            self.save()
        else:
            super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()


class User(AbstractUser, SoftDeleteMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  
    # Extend AbstractUser with additional fields for password reset
    forget_password_token = models.CharField(max_length=255, blank=True, null=True)
    forget_password_expires_at = models.DateTimeField(blank=True, null=True)
    reset_password_token = models.CharField(max_length=255, blank=True, null=True)
    reset_password_expires_at = models.DateTimeField(blank=True, null=True)
    online_status = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user'


class Project(SoftDeleteMixin):
    STATUS_CHOICES = [
            ('pending', 'Pending'),
            ('in-progress', 'In Progress'),
            ('completed', 'Completed')
        ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES,default='pending')  # pending, completed, in-progress
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="owned_projects", blank=True, null=True)
    members = models.ManyToManyField(User, related_name="projects")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'project'

    def __str__(self):
        return self.name


class Task(SoftDeleteMixin):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in-progress', 'In Progress'),
        ('completed', 'Completed')
    ]

    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High')
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES,default='pending')  # pending, completed, in-progress
    priority = models.IntegerField(default=1)  # 1 (low), 2 (medium), 3 (high)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, blank=True, null=True, related_name="tasks")
    assignees = models.ManyToManyField(User, related_name="tasks")
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'task'

    def __str__(self):
        return self.title


class Comment(SoftDeleteMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="comments")
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, blank=True, null=True, related_name="comments")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'comment'

    def __str__(self):
        return f"Comment by {self.author.username} on {self.task.title}"

class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    members = models.ManyToManyField(User, related_name="chat_rooms")  # Quan hệ nhiều-nhiều với User
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'room'

    def __str__(self):
        return f"Room: {self.name}"

class Message(SoftDeleteMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="messages_sent")
    receiver = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="messages_received")
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, blank=True, null=True, related_name="messages")
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'message'

    def __str__(self):
        sender_name = self.sender.username if self.sender else "Unknown"
        return f"Message from {sender_name} in {self.room.name}"


class Notification(SoftDeleteMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="notifications")
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, blank=True, null=True, related_name="notifications", help_text="Liên kết tới nhiệm vụ (nếu có)")
    message = models.TextField(help_text="Nội dung thông báo")
    is_read = models.BooleanField(default=False)
    scheduled_time = models.DateTimeField(blank=True, null=True, help_text="Thời gian dự kiến gửi thông báo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification'

    def __str__(self):
        user_name = self.user.username if self.user else "Unknown"
        return f"Notification for {user_name}"



class RefreshToken(SoftDeleteMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="refresh_token")
    token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'refreshtoken'

    def __str__(self):
        return f"RefreshToken for {self.user.username}"
    

