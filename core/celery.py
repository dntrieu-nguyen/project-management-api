from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Đặt tên dự án của bạn
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

app = Celery("myproject")

# Đọc cấu hình từ Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# Tự động tìm task trong các app
app.autodiscover_tasks()