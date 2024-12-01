from rest_framework import serializers


class CreateCommentTaskSerializers(serializers.Serializer):
    task_id = serializers.CharField(required=True)
    content = serializers.CharField()
    seen = serializers.CharField(required=False, allow_blank=True)

class UpdateCommentTaskByUserSerializers(serializers.Serializer):
    task_id = serializers.CharField(required=True)
    comment_id = serializers.CharField(required=True)
    content = serializers.CharField(required=False,allow_null=True, allow_blank=True)


class UpdateSeenListByUserSerializers(serializers.Serializer):
    task_id = serializers.CharField(required=True)
    comment_id = serializers.CharField(required=True)


class DeletedCommentByUserSerializers(serializers.Serializer):
    task_id = serializers.CharField(required=True)
    comment_id = serializers.CharField(required=True)

class DeletedCommentReplyByUserSerializers(serializers.Serializer):
    task_id = serializers.CharField(required=True)
    comment_id = serializers.CharField(required=True)
    reply_comment_id = serializers.CharField(required=True)

class CreateReplyCommentByUserSerializers(serializers.Serializer):
    task_id = serializers.CharField(required=True)
    comment_id = serializers.CharField(required=True)
    content_reply = serializers.CharField(required = True)

class UpdateReplyCommentByUserSerializers(serializers.Serializer):
    task_id = serializers.CharField(required=True)
    comment_id = serializers.CharField(required=True)
    comment_reply_id = serializers.CharField(required=True)
    content = serializers.CharField(required = True)

class DeleteReplyCommentByUserSerializers(serializers.Serializer):
    task_id = serializers.CharField(required=True)
    comment_id = serializers.CharField(required=True)
    comment_reply_id = serializers.CharField(required=True)