"""Document, search, and analytics API tests."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient

from app.models import Document, Task
from app.services.activity_service import log_activity


pytestmark = pytest.mark.django_db


def _auth_header_for(user):
    from app.authentication import generate_jwt

    return f"Bearer {generate_jwt(user)}"


def test_admin_can_upload_txt_document(admin_user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(admin_user))

    upload = SimpleUploadedFile('guide.txt', b'Hello authentication setup', content_type='text/plain')
    response = client.post('/api/documents', {'file': upload}, format='multipart')

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['filename'] == 'guide.txt'
    assert Document.objects.count() == 1
    assert Document.objects.first().content_text == 'Hello authentication setup'


def test_non_admin_cannot_upload_document(regular_user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(regular_user))

    upload = SimpleUploadedFile('guide.txt', b'Hello', content_type='text/plain')
    response = client.post('/api/documents', {'file': upload}, format='multipart')

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_upload_rejects_non_txt_file(admin_user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(admin_user))

    upload = SimpleUploadedFile('guide.pdf', b'%PDF-1.4', content_type='application/pdf')
    response = client.post('/api/documents', {'file': upload}, format='multipart')

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_authenticated_user_can_list_and_view_document_detail(admin_user, regular_user):
    document = Document.objects.create(
        filename='doc.txt',
        file_path='documents/doc.txt',
        file_size=123,
        uploaded_by=admin_user,
        content_text='x' * 600,
    )

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(regular_user))

    list_response = client.get('/api/documents')
    detail_response = client.get(f'/api/documents/{document.id}')

    assert list_response.status_code == status.HTTP_200_OK
    assert list_response.data['count'] == 1
    assert detail_response.status_code == status.HTTP_200_OK
    assert len(detail_response.data['content_preview']) == 500


def test_search_returns_required_fields(admin_user, regular_user, monkeypatch):
    document = Document.objects.create(
        filename='auth.txt',
        file_path='documents/auth.txt',
        file_size=200,
        uploaded_by=admin_user,
        content_text='Authentication setup instructions for JWT.',
    )

    def fake_search(query, top_k=5):
        return [{'doc_id': document.id, 'score': 0.95}]

    monkeypatch.setattr('app.views.embedding_service.search', fake_search)

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(regular_user))

    response = client.post('/api/search', {'query': 'How to authenticate?', 'top_k': 5}, format='json')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 1
    result = response.data['results'][0]
    assert set(result.keys()) == {'document_id', 'filename', 'relevance_score', 'content_snippet'}


def test_analytics_contains_task_search_and_document_stats(admin_user, regular_user):
    Task.objects.create(
        title='Pending',
        description='A',
        assigned_to=regular_user,
        created_by=admin_user,
        status='pending',
    )
    Task.objects.create(
        title='Completed',
        description='B',
        assigned_to=regular_user,
        created_by=admin_user,
        status='completed',
    )
    Document.objects.create(
        filename='doc1.txt',
        file_path='documents/doc1.txt',
        file_size=1024,
        uploaded_by=admin_user,
        content_text='doc one',
    )

    log_activity(regular_user, 'search', {'query': 'jwt', 'top_k': 5})
    log_activity(regular_user, 'search', {'query': 'jwt', 'top_k': 5})
    log_activity(regular_user, 'search', {'query': 'tasks', 'top_k': 5})

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(admin_user))

    response = client.get('/api/analytics')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['tasks']['total'] == 2
    assert response.data['tasks']['completed'] == 1
    assert response.data['tasks']['pending'] == 1
    assert response.data['documents']['total'] == 1
    assert response.data['searches']['total_queries'] == 3
    assert response.data['searches']['top_queries'][0]['query'] == 'jwt'
    assert response.data['searches']['top_queries'][0]['count'] == 2
