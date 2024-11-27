# Generated by Django 5.1.3 on 2024-11-26 03:54

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0010_remove_notification_message_notification_content_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='notification',
            name='fcm_token',
        ),
        migrations.CreateModel(
            name='Firebase_tokens',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('fcm_token', models.CharField(help_text='Token FCM của thiết bị', max_length=500, unique=True)),
                ('device_name', models.CharField(blank=True, help_text='Tên thiết bị (tuỳ chọn)', max_length=255, null=True)),
                ('last_active', models.DateTimeField(auto_now=True, help_text='Lần cuối thiết bị hoạt động')),
                ('user', models.ForeignKey(help_text='Người dùng sở hữu thiết bị', on_delete=django.db.models.deletion.CASCADE, related_name='devices', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'firebase_tokens',
                'unique_together': {('user', 'fcm_token')},
            },
        ),
    ]