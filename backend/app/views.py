"""
API Views
"""
import io
import json
import os
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils.text import get_valid_filename
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import ActivityLog, Document, Role, Task, User
from .serializers import (
    DocumentSerializer,
    DocumentUploadSerializer,
    SearchRequestSerializer,
    SearchResultSerializer,
    SignupSerializer,
    TaskCreateSerializer,
    TaskSerializer,
    TaskStatusUpdateSerializer,
    UserSerializer,
)
from .authentication import generate_jwt
from .services.activity_service import log_activity
from .services.embedding_service import embedding_service

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None


VALID_TASK_STATUSES = {choice[0] for choice in Task.STATUS_CHOICES}


def _is_admin(user):
    return user.role.role_name == 'admin'


def _extract_snippet(text, limit=500):
    if not text:
        return ''
    return text[:limit]


def _parse_json_details(details):
    if not details:
        return {}
    if isinstance(details, dict):
        return details
    try:
        return json.loads(details)
    except (TypeError, json.JSONDecodeError):
        return {}


def _admin_only(request):
    if not _is_admin(request.user):
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    return None


def _build_file_url(request, file_path):
    relative_url = f"/{settings.MEDIA_URL.strip('/')}/{file_path}"
    return request.build_absolute_uri(relative_url)


def _extract_pdf_text(file_bytes):
    if PdfReader is None:
        raise ValueError('PDF support is unavailable. Install pypdf to enable .pdf uploads.')

    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        pages = []
        for page in reader.pages:
            page_text = page.extract_text() or ''
            if page_text.strip():
                pages.append(page_text)
        return '\n'.join(pages).strip()
    except Exception as exc:
        raise ValueError('Unable to read PDF content.') from exc


def _extract_upload_content(upload_file):
    extension = os.path.splitext(upload_file.name.lower())[1]
    upload_file.seek(0)
    file_bytes = upload_file.read()
    upload_file.seek(0)

    if extension == '.txt':
        return file_bytes.decode('utf-8', errors='replace')
    if extension == '.pdf':
        extracted = _extract_pdf_text(file_bytes)
        if not extracted:
            raise ValueError('No readable text found in PDF file.')
        return extracted

    raise ValueError('Only .txt and .pdf files are allowed.')


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """User login endpoint"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({'error': 'Username and password required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    if not user.check_password(password):
        log_activity(user, 'login_failed', {'username': username})
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    token = generate_jwt(user)
    log_activity(user, 'login', {'username': user.username})
    return Response(
        {
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role.role_name,
            },
        },
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    """User/admin signup endpoint."""
    serializer = SignupSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    role_name = serializer.validated_data['role']
    role, _ = Role.objects.get_or_create(role_name=role_name)

    user = User.objects.create_user(
        username=serializer.validated_data['username'],
        email=serializer.validated_data['email'],
        password=serializer.validated_data['password'],
        role=role,
    )

    token = generate_jwt(user)
    log_activity(
        user,
        'signup',
        {
            'role': role_name,
            'username': user.username,
        },
    )

    return Response(
        {
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role.role_name,
            },
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def tasks_endpoint(request):
    """Get tasks with filtering or create a task (admin only)."""
    if request.method == 'POST':
        admin_response = _admin_only(request)
        if admin_response is not None:
            return admin_response

        serializer = TaskCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        task = serializer.save(created_by=request.user)
        log_activity(
            request.user,
            'task_create',
            {
                'task_id': task.id,
                'assigned_to': task.assigned_to_id,
                'status': task.status,
            },
        )
        return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)

    user = request.user

    # Admin can see all tasks, users see only their tasks
    if _is_admin(user):
        tasks = Task.objects.select_related('assigned_to', 'created_by').all()
    else:
        tasks = Task.objects.select_related('assigned_to', 'created_by').filter(assigned_to=user)

    # Apply filters
    status_filter = request.query_params.get('status')
    if status_filter:
        if status_filter not in VALID_TASK_STATUSES:
            return Response({'error': 'Invalid status filter value'}, status=status.HTTP_400_BAD_REQUEST)
        tasks = tasks.filter(status=status_filter)

    assigned_to_filter = request.query_params.get('assigned_to')
    if assigned_to_filter:
        if not _is_admin(user):
            return Response(
                {'error': 'Only admins can filter by assigned_to'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not assigned_to_filter.isdigit():
            return Response({'error': 'assigned_to must be a valid user id'}, status=status.HTTP_400_BAD_REQUEST)
        tasks = tasks.filter(assigned_to_id=int(assigned_to_filter))

    serializer = TaskSerializer(tasks, many=True)
    return Response({'tasks': serializer.data, 'count': tasks.count()}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_task(request):
    """Backward-compatible route for task creation."""
    return tasks_endpoint(request)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_task(request, task_id):
    """Update task status"""
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

    # Users can only update their own tasks
    if not _is_admin(request.user) and task.assigned_to != request.user:
        return Response({'error': 'Cannot update tasks assigned to others'}, status=status.HTTP_403_FORBIDDEN)

    serializer = TaskStatusUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    new_status = serializer.validated_data['status']
    if task.status == 'completed' and new_status == 'pending':
        return Response(
            {'error': 'Invalid status transition. Completed tasks cannot move back to pending.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    task.status = new_status
    task.save(update_fields=['status', 'updated_at'])
    log_activity(
        request.user,
        'task_update',
        {
            'task_id': task.id,
            'new_status': new_status,
        },
    )

    return Response(TaskSerializer(task).data, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def documents_endpoint(request):
    """List all documents or upload a new document (admin only)."""
    if request.method == 'POST':
        admin_response = _admin_only(request)
        if admin_response is not None:
            return admin_response

        upload_serializer = DocumentUploadSerializer(data=request.data)
        if not upload_serializer.is_valid():
            return Response(upload_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        upload_file = upload_serializer.validated_data['file']
        extension = os.path.splitext(upload_file.name.lower())[1]
        if extension not in {'.txt', '.pdf'}:
            return Response({'error': 'Only .txt and .pdf files are allowed'}, status=status.HTTP_400_BAD_REQUEST)

        max_size = 1024 * 1024 * settings.MAX_UPLOAD_SIZE_MB
        if upload_file.size > max_size:
            return Response(
                {'error': f'File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB}MB'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            content_text = _extract_upload_content(upload_file)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        safe_name = get_valid_filename(upload_file.name)
        storage_path = default_storage.save(f'documents/{safe_name}', upload_file)

        document = Document.objects.create(
            filename=safe_name,
            file_path=storage_path,
            file_size=upload_file.size,
            uploaded_by=request.user,
            content_text=content_text,
        )
        embedding_service.add_document(document.id, content_text)

        log_activity(
            request.user,
            'document_upload',
            {
                'document_id': document.id,
                'filename': document.filename,
                'file_type': extension,
            },
        )
        return Response(DocumentSerializer(document, context={'request': request}).data, status=status.HTTP_201_CREATED)

    documents = Document.objects.select_related('uploaded_by').all().order_by('-upload_date')
    serializer = DocumentSerializer(documents, many=True, context={'request': request})
    return Response({'documents': serializer.data, 'count': documents.count()}, status=status.HTTP_200_OK)


@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def get_document_detail(request, document_id):
    """Get details for a single document."""
    try:
        document = Document.objects.select_related('uploaded_by').get(id=document_id)
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        admin_response = _admin_only(request)
        if admin_response is not None:
            return admin_response

        removed_document_id = document.id
        removed_filename = document.filename
        removed_file_path = document.file_path

        if removed_file_path and default_storage.exists(removed_file_path):
            default_storage.delete(removed_file_path)

        document.delete()

        remaining_documents = list(Document.objects.values_list('id', 'content_text'))
        embedding_service.rebuild_index(remaining_documents)

        log_activity(
            request.user,
            'document_delete',
            {
                'document_id': removed_document_id,
                'filename': removed_filename,
            },
        )
        return Response({'message': 'Document deleted successfully'}, status=status.HTTP_200_OK)

    return Response(
        {
            'id': document.id,
            'filename': document.filename,
            'file_size': document.file_size,
            'uploaded_by': document.uploaded_by_id,
            'uploaded_by_username': document.uploaded_by.username,
            'upload_date': document.upload_date,
            'file_url': _build_file_url(request, document.file_path),
            'content_text': document.content_text,
            'content_preview': _extract_snippet(document.content_text),
        },
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search_documents(request):
    """Semantic search across uploaded documents."""
    serializer = SearchRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    query = serializer.validated_data['query']
    top_k = serializer.validated_data['top_k']
    search_hits = embedding_service.search(query, top_k=top_k)

    hit_doc_ids = [hit['doc_id'] for hit in search_hits]
    documents = {doc.id: doc for doc in Document.objects.filter(id__in=hit_doc_ids)}

    formatted_results = []
    for hit in search_hits:
        document = documents.get(hit['doc_id'])
        if not document:
            continue

        formatted_results.append(
            {
                'document_id': document.id,
                'filename': document.filename,
                'relevance_score': round(hit['score'], 6),
                'content_snippet': _extract_snippet(document.content_text, limit=300),
            }
        )

    result_serializer = SearchResultSerializer(data=formatted_results, many=True)
    result_serializer.is_valid(raise_exception=True)

    log_activity(
        request.user,
        'search',
        {
            'query': query,
            'top_k': top_k,
            'result_count': len(result_serializer.data),
        },
    )

    return Response(
        {
            'query': query,
            'results': result_serializer.data,
            'count': len(result_serializer.data),
        },
        status=status.HTTP_200_OK,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_analytics(request):
    """Get system analytics (admin only)"""
    admin_response = _admin_only(request)
    if admin_response is not None:
        return admin_response

    total_tasks = Task.objects.count()
    completed_tasks = Task.objects.filter(status='completed').count()
    pending_tasks = Task.objects.filter(status='pending').count()

    search_logs = ActivityLog.objects.filter(action_type='search').order_by('-timestamp')
    query_counter = {}
    for log_entry in search_logs:
        query = _parse_json_details(log_entry.details).get('query')
        if query:
            query_counter[query] = query_counter.get(query, 0) + 1

    top_queries = sorted(query_counter.items(), key=lambda item: item[1], reverse=True)[:5]
    top_query_payload = [{'query': query, 'count': count} for query, count in top_queries]

    total_document_size = sum(Document.objects.values_list('file_size', flat=True))
    document_count = Document.objects.count()

    return Response(
        {
            'tasks': {
                'total': total_tasks,
                'completed': completed_tasks,
                'pending': pending_tasks,
            },
            'searches': {
                'total_queries': sum(query_counter.values()),
                'top_queries': top_query_payload,
            },
            'documents': {
                'total': document_count,
                'total_size_mb': round((total_document_size / (1024 * 1024)) if total_document_size else 0.0, 2),
            },
        },
        status=status.HTTP_200_OK,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """Get current authenticated user profile."""
    return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_users(request):
    """List users for admin assignment workflows."""
    admin_response = _admin_only(request)
    if admin_response is not None:
        return admin_response

    users = User.objects.select_related('role').all().order_by('username')
    serializer = UserSerializer(users, many=True)
    return Response({'users': serializer.data, 'count': users.count()}, status=status.HTTP_200_OK)
