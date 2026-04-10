"""
Serializers for API endpoints
"""
from django.conf import settings
from rest_framework import serializers
from .models import User, Role, Task, Document, ActivityLog


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'role_name', 'created_at']


class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='role.role_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100)
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(min_length=8, max_length=128, write_only=True)
    role = serializers.ChoiceField(choices=['user', 'admin'], required=False, default='user')
    admin_signup_code = serializers.CharField(required=False, allow_blank=True, write_only=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Username is already taken.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email is already registered.')
        return value

    def validate(self, attrs):
        role = attrs.get('role', 'user')
        if role == 'admin':
            code = attrs.get('admin_signup_code', '')
            if not settings.ADMIN_SIGNUP_CODE:
                raise serializers.ValidationError({'role': 'Admin signup is disabled.'})
            if code != settings.ADMIN_SIGNUP_CODE:
                raise serializers.ValidationError({'admin_signup_code': 'Invalid admin signup code.'})
        return attrs


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'assigned_to', 'created_by', 
                  'assigned_to_username', 'created_by_username',
                  'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class TaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'assigned_to', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_status(self, value):
        if value != 'pending':
            raise serializers.ValidationError("Task status must be 'pending' on creation.")
        return value


class TaskStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[('pending', 'Pending'), ('completed', 'Completed')])


class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ['id', 'filename', 'file_path', 'file_size', 'uploaded_by', 
                  'uploaded_by_username', 'upload_date', 'content_text', 'file_url']
        read_only_fields = ['id', 'uploaded_by', 'upload_date']

    def get_file_url(self, obj):
        request = self.context.get('request') if hasattr(self, 'context') else None
        relative_url = f"/{settings.MEDIA_URL.strip('/')}/{obj.file_path}"
        if request is not None:
            return request.build_absolute_uri(relative_url)
        return relative_url


class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)


class SearchRequestSerializer(serializers.Serializer):
    query = serializers.CharField(min_length=1, max_length=2000)
    top_k = serializers.IntegerField(min_value=1, max_value=50, required=False, default=5)


class SearchResultSerializer(serializers.Serializer):
    document_id = serializers.IntegerField()
    filename = serializers.CharField()
    relevance_score = serializers.FloatField()
    content_snippet = serializers.CharField()


class ActivityLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = ActivityLog
        fields = ['id', 'user', 'username', 'action_type', 'details', 'timestamp']
        read_only_fields = ['id', 'timestamp']
