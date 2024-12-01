import datetime
import uuid
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework import status
from app.models import Project, User, Task
from comments.serializers import CreateCommentTaskSerializers, CreateReplyCommentByUserSerializers, DeleteReplyCommentByUserSerializers, DeletedCommentByUserSerializers, UpdateCommentTaskByUserSerializers, UpdateReplyCommentByUserSerializers, UpdateSeenListByUserSerializers
from middlewares import auth_middleware
from utils.response import failure_response, success_response
from firebase.firebase_config import db

# Create your views here.
@api_view(['POST'])
@auth_middleware
def create_comment_task_by_user(request):
    try:
        user_id = request.user['id']
        req_body = CreateCommentTaskSerializers(data=request.data)

        # Validate request body
        if not req_body.is_valid():
            return failure_response(message="Validation Errors", data=req_body.errors)

        # Extract validated data
        task_id = req_body.validated_data['task_id']
        try:
            # Ensure task_id is a valid UUID
            task_uuid = uuid.UUID(task_id)
        except ValueError:
            return failure_response(message="Invalid Task ID format")

        # Check if the task exists
        is_exist_task = Task.objects.filter(id=task_uuid).exists()
        if not is_exist_task:
            return failure_response(message="Task not found")

        # Validate seen list
        seen_list = req_body.validated_data.get('seen', '')
        if seen_list:  
            seen_ids = seen_list.split(',')
            seen_users = User.objects.filter(id__in=seen_ids)
            if len(seen_ids) != seen_users.count():
                return failure_response(message="One or more users in 'seen' list not found. Please check again.")

        # Prepare comment data
        new_data = {
            'content': req_body.validated_data['content'],
            'updated_at': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'created_at': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'seen': req_body.validated_data.get('seen', ''),
            'user_id': user_id,
        }

        # Push data to Firebase
        ref = db.reference(f'comments/{task_id}')
        snapshot = ref.push(new_data)

        return success_response(
            message="Comment created successfully",
            status_code=status.HTTP_201_CREATED,
            data={"id": snapshot.key, "comment_data": new_data}
        )
    except Exception as e:
        return failure_response(message="An unexpected error occurred", data=str(e))

# update content
@api_view(['PATCH', 'DELETE'])
@auth_middleware
def update_comment_by_user(request):    
    try:
      
        user_id = request.user['id']
        req_body = UpdateCommentTaskByUserSerializers(data = request.data)

        if not req_body.is_valid():
            return failure_response(message="Validations Errors", data= req_body.errors)

        ref = db.reference(f'comments/{req_body.validated_data['task_id']}/{req_body.validated_data['comment_id']}')
        task_id = req_body.validated_data['task_id']

        try:
            # Ensure task_id is a valid UUID
            task_uuid = uuid.UUID(task_id)
        except ValueError:
            return failure_response(message="Invalid Task ID format")
        
        # check permissions
        latest_data = ref.get()

        if latest_data['user_id'] != user_id:
            return failure_response(
                message="User have not permission for this action",
                status_code=status.HTTP_406_NOT_ACCEPTABLE
            )
        
            
        # Check if the task exists
        is_exist_task = Task.objects.filter(id=task_uuid).exists()
        if not is_exist_task:
            return failure_response(message="Task not found")
      
        # Update data
        new_data = {
            'content': latest_data['content'] if not bool(request.data['content']) else req_body.validated_data['content'] ,
            'updated_at': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'user_id': user_id,
        }
        ref.update(new_data)
        return success_response(
                message="Comment updated successfully",
                status_code=status.HTTP_201_CREATED,
                data=new_data
            )
    except Exception as e:
      return failure_response(message="An unexpected error occurred", data=str(e))
    
# delete comment by user
@api_view(['DELETE'])
@auth_middleware
def delete_comment_by_user(request):
    try:
        req_body = DeletedCommentByUserSerializers(data = request.data)
        user_id = request.user['id']
        if not req_body.is_valid():
            return failure_response(
                message="Validations Errors",
                data= req_body.errors
            )
        
        validated_data = req_body.validated_data
        ref = db.reference(f"comments/{validated_data['task_id']}/{validated_data['comment_id']}")
        try:
            task_uuid = uuid.UUID(validated_data['task_id'])
        except ValueError:
            return failure_response(message="Invalid Task ID format")
        
        # Check if the task exists
        is_exist_task = Task.objects.filter(id=task_uuid).exists()
        if not is_exist_task:
            return failure_response(message="Task not found")
        
        # check permissions
        latest_data = ref.get()

        if latest_data['user_id'] != user_id:
            return failure_response(
                message="User have not permission for this action",
                status_code=status.HTTP_406_NOT_ACCEPTABLE
            )
        
        
        # Validate ok
        ref.delete()
        
        
        return success_response(message="Delete comment succesfully", data=latest_data)
    except Exception as e:
        return failure_response(message="An unexpected error occurred", data=str(e))

# create reply comment by user
@api_view(['POST'])
@auth_middleware
def create_reply_comment_by_user(request):
    try:
        req_body = CreateReplyCommentByUserSerializers(data=request.data)
        user_id = request.user['id']
        if not req_body.is_valid():
            return failure_response(
                message="Validations Errors",
                data= req_body.errors
            )
        validated_data =  req_body.validated_data
        ref = db.reference(f"comments/{validated_data['task_id']}/{validated_data['comment_id']}")
        # Check task uuid
        try:
            task_uuid = uuid.UUID(validated_data['task_id'])
        except ValueError:
            return failure_response(message="Invalid Task ID format")
        
        # Check if the task exists
        is_exist_task = Task.objects.filter(id=task_uuid).exists()
        if not is_exist_task:
            return failure_response(message="Task not found")
        
        reply_ref = db.reference(f"comments/{validated_data['task_id']}/{validated_data['comment_id']}/replies")
        
        new_reply_data = {
            "user_id": user_id,
            "created_at": datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            "updated_at": datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            "content": validated_data['content_reply']
        }
        reply_ref.push(new_reply_data)

        return success_response(
            message="Reply this comment successfully",
        )
    except Exception as e:
        return failure_response(message="An unexpected error occurred", data=str(e))

# update reply comment by user   
@api_view(['PATCH','DELETE'])
@auth_middleware
def update_reply_comment_by_user(request):
    try:
        req_body = UpdateReplyCommentByUserSerializers(data=request.data)
        user_id = request.user['id']
        if not req_body.is_valid():
            return failure_response(
                message="Validations Errors",
                data= req_body.errors
            )
        validated_data =  req_body.validated_data
        ref = db.reference(f"comments/{validated_data['task_id']}/{validated_data['comment_id']}")
        # Check task uuid
        try:
            task_uuid = uuid.UUID(validated_data['task_id'])
        except ValueError:
            return failure_response(message="Invalid Task ID format")
        
        # Check if the task exists
        is_exist_task = Task.objects.filter(id=task_uuid).exists()
        if not is_exist_task:
            return failure_response(message="Task not found")
        
        reply_ref = db.reference(f"comments/{validated_data['task_id']}/{validated_data['comment_id']}/replies/{validated_data['comment_reply_id']}")
        latest_reply_comment = reply_ref.get()

        # check permission
        if not user_id == latest_reply_comment['user_id']:
            return failure_response(
                message="you dont have permission for this action",
                status_code= status.HTTP_403_FORBIDDEN
            )
        update_data = {
            "content": validated_data['content'],
            "updated_at": datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        }

        reply_ref.update(update_data)

        
        return success_response(message="update comment successfully")
    except Exception as e:
        return failure_response(message="An unexpected error occurred", data=str(e))
        

# delete reply comment by user
@api_view(['DELETE'])
@auth_middleware
def delete_reply_comment_by_user(request):
    try:
        req_body = DeleteReplyCommentByUserSerializers(data=request.data)
        user_id = request.user['id']
        if not req_body.is_valid():
            return failure_response(
                message="Validations Errors",
                data= req_body.errors
            )
        validated_data =  req_body.validated_data
        ref = db.reference(f"comments/{validated_data['task_id']}/{validated_data['comment_id']}")
        # Check task uuid
        try:
            task_uuid = uuid.UUID(validated_data['task_id'])
        except ValueError:
            return failure_response(message="Invalid Task ID format")
        
        # Check if the task exists
        is_exist_task = Task.objects.filter(id=task_uuid).exists()
        if not is_exist_task:
            return failure_response(message="Task not found")
        
        reply_ref = db.reference(f"comments/{validated_data['task_id']}/{validated_data['comment_id']}/replies/{validated_data['comment_reply_id']}")
        latest_reply_comment = reply_ref.get()

        # check permission
        if not user_id == latest_reply_comment['user_id']:
            return failure_response(
                message="you dont have permission for this action",
                status_code= status.HTTP_403_FORBIDDEN
            )
        reply_ref.delete()
        return success_response(message="delete reply comment successfully")
    except Exception as e:
        return failure_response(message="An unexpected error occurred", data=str(e))