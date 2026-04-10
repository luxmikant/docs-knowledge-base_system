"""Property-based tests for documents, search, embeddings, logging, and analytics."""

import os
import tempfile

import numpy as np
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from hypothesis import given, settings as hy_settings, strategies as st
from rest_framework import status
from rest_framework.test import APIClient

from app.models import ActivityLog, Document, Role, Task, User
from app.services.activity_service import log_activity
from app.services.embedding_service import EmbeddingService


pytestmark = pytest.mark.django_db


CONTENT_STRATEGY = st.text(min_size=1, max_size=400, alphabet=st.characters(whitelist_categories=['Ll', 'Lu', 'Nd', 'Zs', 'Po']))
QUERY_STRATEGY = st.text(min_size=3, max_size=40, alphabet=st.characters(whitelist_categories=['Ll', 'Lu', 'Nd', 'Zs']))


def _auth_header_for(user):
    from app.authentication import generate_jwt

    return f"Bearer {generate_jwt(user)}"


def _create_roles():
    admin_role, _ = Role.objects.get_or_create(role_name='admin')
    user_role, _ = Role.objects.get_or_create(role_name='user')
    return admin_role, user_role


def _create_unique_user(role, prefix, password):
    base_username = f'{prefix}_{User.objects.count()}'
    username = base_username
    suffix = 1
    while User.objects.filter(username=username).exists():
        username = f'{base_username}_{suffix}'
        suffix += 1

    email = f'{username}@example.com'
    email_suffix = 1
    while User.objects.filter(email=email).exists():
        email = f'{username}+{email_suffix}@example.com'
        email_suffix += 1

    return User.objects.create_user(
        username=username,
        email=email,
        password=password,
        role=role,
    )


@hy_settings(max_examples=100, deadline=None)
@given(filename=st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=['Ll', 'Lu', 'Nd'])), content=CONTENT_STRATEGY)
def test_document_metadata_persistence_property(filename, content):
    """Property 5: Document metadata persists and is retrievable by ID."""
    # Property: 5
    admin_role, _ = _create_roles()
    admin_user = _create_unique_user(admin_role, 'admin_meta', 'AdminPass123')

    document = Document.objects.create(
        filename=f'{filename}.txt',
        file_path=f'documents/{filename}.txt',
        file_size=len(content.encode('utf-8')),
        uploaded_by=admin_user,
        content_text=content,
    )

    loaded = Document.objects.get(id=document.id)
    assert loaded.filename == f'{filename}.txt'
    assert loaded.file_size == len(content.encode('utf-8'))
    assert loaded.uploaded_by_id == admin_user.id
    assert loaded.upload_date is not None


@hy_settings(max_examples=100, deadline=None)
@given(content=CONTENT_STRATEGY)
def test_document_content_extraction_property(content):
    """Property 6: Uploaded .txt content is extracted and stored accurately."""
    # Property: 6
    admin_role, _ = _create_roles()
    admin_user = _create_unique_user(admin_role, 'admin_extract', 'AdminPass123')

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(admin_user))

    upload = SimpleUploadedFile('content.txt', content.encode('utf-8'), content_type='text/plain')
    response = client.post('/api/documents', {'file': upload}, format='multipart')

    assert response.status_code == status.HTTP_201_CREATED
    document = Document.objects.get(id=response.data['id'])
    assert document.content_text == content


@hy_settings(max_examples=100, deadline=None)
@given(text=CONTENT_STRATEGY)
def test_embedding_generation_consistency_property(text):
    """Property 7: Embeddings are 384-dim and consistent for same input."""
    # Property: 7
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ['DISABLE_TRANSFORMER_MODEL'] = 'true'
        from django.conf import settings

        previous_path = settings.FAISS_INDEX_PATH
        settings.FAISS_INDEX_PATH = temp_dir
        service = EmbeddingService()

        embedding_a = service.generate_embedding(text)
        embedding_b = service.generate_embedding(text)

        assert embedding_a.shape[0] == 384
        assert embedding_b.shape[0] == 384

        similarity = float(np.dot(embedding_a, embedding_b) / (np.linalg.norm(embedding_a) * np.linalg.norm(embedding_b)))
        assert similarity > 0.99
        settings.FAISS_INDEX_PATH = previous_path


@hy_settings(max_examples=100, deadline=None)
@given(text=CONTENT_STRATEGY)
def test_embedding_storage_retrieval_property(text):
    """Property 8: Stored embeddings are retrievable via search."""
    # Property: 8
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ['DISABLE_TRANSFORMER_MODEL'] = 'true'
        from django.conf import settings

        previous_path = settings.FAISS_INDEX_PATH
        settings.FAISS_INDEX_PATH = temp_dir
        service = EmbeddingService()

        service.add_document(101, text)
        results = service.search(text, top_k=5)

        assert any(result['doc_id'] == 101 for result in results)
        settings.FAISS_INDEX_PATH = previous_path


@hy_settings(max_examples=100, deadline=None)
@given(top_k=st.integers(min_value=1, max_value=10), document_count=st.integers(min_value=1, max_value=7))
def test_search_result_cardinality_property(top_k, document_count, monkeypatch):
    """Property 9: Search returns at most top_k and all docs when fewer exist."""
    # Property: 9
    admin_role, user_role = _create_roles()
    admin_user = _create_unique_user(admin_role, 'admin_card', 'AdminPass123')
    requester = _create_unique_user(user_role, 'user_card', 'UserPass123')

    doc_ids = []
    for index in range(document_count):
        document = Document.objects.create(
            filename=f'card_{index}.txt',
            file_path=f'documents/card_{index}.txt',
            file_size=30,
            uploaded_by=admin_user,
            content_text=f'content {index}',
        )
        doc_ids.append(document.id)

    def fake_search(query, top_k=5):
        selected = doc_ids[: min(top_k, len(doc_ids))]
        return [{'doc_id': doc_id, 'score': 0.9 - idx * 0.01} for idx, doc_id in enumerate(selected)]

    monkeypatch.setattr('app.views.embedding_service.search', fake_search)

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(requester))
    response = client.post('/api/search', {'query': 'content', 'top_k': top_k}, format='json')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] <= top_k
    assert response.data['count'] == min(top_k, document_count)


@hy_settings(max_examples=100, deadline=None)
@given(query=QUERY_STRATEGY)
def test_search_result_completeness_property(query, monkeypatch):
    """Property 10: Search results include all required fields."""
    # Property: 10
    admin_role, user_role = _create_roles()
    admin_user = _create_unique_user(admin_role, 'admin_complete', 'AdminPass123')
    requester = _create_unique_user(user_role, 'user_complete', 'UserPass123')
    document = Document.objects.create(
        filename='complete.txt',
        file_path='documents/complete.txt',
        file_size=80,
        uploaded_by=admin_user,
        content_text='completeness test content',
    )

    monkeypatch.setattr('app.views.embedding_service.search', lambda q, top_k=5: [{'doc_id': document.id, 'score': 0.88}])

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(requester))
    response = client.post('/api/search', {'query': query, 'top_k': 5}, format='json')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] >= 1
    result = response.data['results'][0]
    assert set(result.keys()) == {'document_id', 'filename', 'relevance_score', 'content_snippet'}


@hy_settings(max_examples=100, deadline=None)
@given(search_query=QUERY_STRATEGY)
def test_activity_logging_completeness_property(search_query):
    """Property 17: Key actions generate activity log entries."""
    # Property: 17
    admin_role, user_role = _create_roles()
    admin_user = _create_unique_user(admin_role, 'admin_log', 'AdminPass123')
    user = _create_unique_user(user_role, 'user_log', 'UserPass123')

    # Login action
    client = APIClient()
    login_response = client.post('/api/auth/login', {'username': user.username, 'password': 'UserPass123'}, format='json')
    assert login_response.status_code == status.HTTP_200_OK

    # Task creation and update actions
    admin_client = APIClient()
    admin_client.credentials(HTTP_AUTHORIZATION=_auth_header_for(admin_user))
    create_response = admin_client.post(
        '/api/tasks',
        {'title': 'log task', 'description': 'd', 'assigned_to': user.id, 'status': 'pending'},
        format='json',
    )
    assert create_response.status_code == status.HTTP_201_CREATED

    user_client = APIClient()
    user_client.credentials(HTTP_AUTHORIZATION=_auth_header_for(user))
    update_response = user_client.put(f"/api/tasks/{create_response.data['id']}", {'status': 'completed'}, format='json')
    assert update_response.status_code == status.HTTP_200_OK

    # Search action
    log_activity(user, 'search', {'query': search_query, 'top_k': 5})

    action_types = set(ActivityLog.objects.filter(user=user).values_list('action_type', flat=True))
    assert 'login' in action_types
    assert 'task_update' in action_types
    assert 'search' in action_types


@hy_settings(max_examples=100, deadline=None)
@given(
    pending_count=st.integers(min_value=1, max_value=5),
    completed_count=st.integers(min_value=1, max_value=5),
)
def test_analytics_count_accuracy_property(pending_count, completed_count):
    """Property 18: Analytics task counts are accurate and total is consistent."""
    # Property: 18
    admin_role, user_role = _create_roles()
    admin_user = _create_unique_user(admin_role, 'admin_analytics', 'AdminPass123')
    assignee = _create_unique_user(user_role, 'user_analytics', 'UserPass123')

    for index in range(pending_count):
        Task.objects.create(
            title=f'pending_{index}',
            description='p',
            assigned_to=assignee,
            created_by=admin_user,
            status='pending',
        )

    for index in range(completed_count):
        Task.objects.create(
            title=f'completed_{index}',
            description='c',
            assigned_to=assignee,
            created_by=admin_user,
            status='completed',
        )

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(admin_user))
    response = client.get('/api/analytics')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['tasks']['total'] == pending_count + completed_count
    assert response.data['tasks']['completed'] == completed_count
    assert response.data['tasks']['pending'] == pending_count


@hy_settings(max_examples=100, deadline=None)
@given(queries=st.lists(QUERY_STRATEGY, min_size=3, max_size=10))
def test_search_query_frequency_tracking_property(queries):
    """Property 19: Analytics search query frequency is accurate."""
    # Property: 19
    admin_role, user_role = _create_roles()
    admin_user = _create_unique_user(admin_role, 'admin_freq', 'AdminPass123')
    user = _create_unique_user(user_role, 'user_freq', 'UserPass123')

    expected_counts = {}
    for query in queries:
        log_activity(user, 'search', {'query': query, 'top_k': 5})
        expected_counts[query] = expected_counts.get(query, 0) + 1

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(admin_user))
    response = client.get('/api/analytics')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['searches']['total_queries'] == len(queries)

    if response.data['searches']['top_queries']:
        top_entry = response.data['searches']['top_queries'][0]
        expected_top_count = max(expected_counts.values())
        assert top_entry['count'] == expected_top_count


@hy_settings(max_examples=100, deadline=None)
@given(score_triplet=st.lists(st.floats(min_value=0.1, max_value=1.0, allow_nan=False, allow_infinity=False), min_size=3, max_size=3))
def test_semantic_search_relevance_ordering_property(score_triplet, monkeypatch):
    """Property 20: Search results are ordered by descending relevance score."""
    # Property: 20
    admin_role, user_role = _create_roles()
    admin_user = _create_unique_user(admin_role, 'admin_relevance', 'AdminPass123')
    requester = _create_unique_user(user_role, 'user_relevance', 'UserPass123')

    documents = []
    for index in range(3):
        documents.append(
            Document.objects.create(
                filename=f'relevance_{index}.txt',
                file_path=f'documents/relevance_{index}.txt',
                file_size=80,
                uploaded_by=admin_user,
                content_text='semantic content',
            )
        )

    ordered_scores = sorted([abs(value) for value in score_triplet], reverse=True)

    def fake_search(query, top_k=5):
        return [
            {'doc_id': documents[index].id, 'score': ordered_scores[index]}
            for index in range(3)
        ]

    monkeypatch.setattr('app.views.embedding_service.search', fake_search)

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(requester))
    response = client.post('/api/search', {'query': 'semantic', 'top_k': 3}, format='json')

    assert response.status_code == status.HTTP_200_OK
    returned_scores = [result['relevance_score'] for result in response.data['results']]
    assert returned_scores == sorted(returned_scores, reverse=True)
