"""Task management API tests."""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from app.models import Task, User


pytestmark = pytest.mark.django_db


def _auth_header_for(user):
    from app.authentication import generate_jwt

    return f"Bearer {generate_jwt(user)}"


def test_admin_can_create_task(admin_user, regular_user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(admin_user))

    response = client.post(
        '/api/tasks',
        {
            'title': 'Review architecture',
            'description': 'Read design docs',
            'assigned_to': regular_user.id,
            'status': 'pending',
        },
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['title'] == 'Review architecture'
    assert response.data['assigned_to'] == regular_user.id
    assert Task.objects.count() == 1


def test_non_admin_cannot_create_task(regular_user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(regular_user))

    response = client.post(
        '/api/tasks',
        {
            'title': 'Should fail',
            'description': 'No admin role',
            'assigned_to': regular_user.id,
            'status': 'pending',
        },
        format='json',
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_task_creation_rejects_invalid_assigned_user(admin_user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(admin_user))

    response = client.post(
        '/api/tasks',
        {
            'title': 'Bad assignment',
            'description': 'Invalid user id',
            'assigned_to': 999999,
            'status': 'pending',
        },
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_user_sees_only_assigned_tasks(admin_user, regular_user, user_role):
    another_user = User.objects.create_user(
        username='user2',
        email='user2@test.com',
        password='user123',
        role=user_role,
    )

    Task.objects.create(
        title='Task for user1',
        description='A',
        assigned_to=regular_user,
        created_by=admin_user,
        status='pending',
    )
    Task.objects.create(
        title='Task for user2',
        description='B',
        assigned_to=another_user,
        created_by=admin_user,
        status='pending',
    )

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(regular_user))

    response = client.get('/api/tasks')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 1
    assert response.data['tasks'][0]['assigned_to'] == regular_user.id


def test_admin_filtering_by_status_and_assigned_to(admin_user, regular_user, user_role):
    another_user = User.objects.create_user(
        username='user3',
        email='user3@test.com',
        password='user123',
        role=user_role,
    )

    Task.objects.create(
        title='Pending for user1',
        description='A',
        assigned_to=regular_user,
        created_by=admin_user,
        status='pending',
    )
    Task.objects.create(
        title='Completed for user1',
        description='B',
        assigned_to=regular_user,
        created_by=admin_user,
        status='completed',
    )
    Task.objects.create(
        title='Pending for user3',
        description='C',
        assigned_to=another_user,
        created_by=admin_user,
        status='pending',
    )

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(admin_user))

    response = client.get(f'/api/tasks?status=pending&assigned_to={regular_user.id}')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 1
    assert response.data['tasks'][0]['title'] == 'Pending for user1'


def test_invalid_status_filter_returns_400(admin_user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(admin_user))

    response = client.get('/api/tasks?status=invalid')

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_user_cannot_filter_assigned_to(regular_user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(regular_user))

    response = client.get('/api/tasks?assigned_to=1')

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_assigned_user_can_update_task_status(admin_user, regular_user):
    task = Task.objects.create(
        title='Update status',
        description='A',
        assigned_to=regular_user,
        created_by=admin_user,
        status='pending',
    )

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(regular_user))

    response = client.put(f'/api/tasks/{task.id}', {'status': 'completed'}, format='json')

    task.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert task.status == 'completed'


def test_user_cannot_update_other_users_task(admin_user, regular_user, user_role):
    another_user = User.objects.create_user(
        username='user4',
        email='user4@test.com',
        password='user123',
        role=user_role,
    )
    task = Task.objects.create(
        title='Protected task',
        description='A',
        assigned_to=another_user,
        created_by=admin_user,
        status='pending',
    )

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(regular_user))

    response = client.put(f'/api/tasks/{task.id}', {'status': 'completed'}, format='json')

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_invalid_status_transition_is_rejected(admin_user, regular_user):
    task = Task.objects.create(
        title='Completed task',
        description='A',
        assigned_to=regular_user,
        created_by=admin_user,
        status='completed',
    )

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(regular_user))

    response = client.put(f'/api/tasks/{task.id}', {'status': 'pending'}, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
