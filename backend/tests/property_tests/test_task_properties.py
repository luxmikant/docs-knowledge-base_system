"""Property-based tests for task management."""

import pytest
from hypothesis import given, settings as hy_settings, strategies as st
from rest_framework import status
from rest_framework.test import APIClient

from app.models import Role, Task, User


pytestmark = pytest.mark.django_db


TITLE_STRATEGY = st.text(min_size=3, max_size=60, alphabet=st.characters(whitelist_categories=['Ll', 'Lu', 'Nd', 'Zs']))
DESCRIPTION_STRATEGY = st.text(min_size=0, max_size=200, alphabet=st.characters(whitelist_categories=['Ll', 'Lu', 'Nd', 'Zs', 'Po']))


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
@given(title=TITLE_STRATEGY, description=DESCRIPTION_STRATEGY)
def test_task_creation_and_assignment_property(title, description):
    """Property 11: Admin can create tasks and assignee can retrieve them."""
    # Property: 11
    admin_role, user_role = _create_roles()
    admin_user = _create_unique_user(admin_role, 'admin_task_create', 'AdminPass123')
    assigned_user = _create_unique_user(user_role, 'assignee', 'UserPass123')

    admin_client = APIClient()
    admin_client.credentials(HTTP_AUTHORIZATION=_auth_header_for(admin_user))
    create_response = admin_client.post(
        '/api/tasks',
        {'title': title, 'description': description, 'assigned_to': assigned_user.id, 'status': 'pending'},
        format='json',
    )

    assert create_response.status_code == status.HTTP_201_CREATED

    assignee_client = APIClient()
    assignee_client.credentials(HTTP_AUTHORIZATION=_auth_header_for(assigned_user))
    list_response = assignee_client.get('/api/tasks')

    assert list_response.status_code == status.HTTP_200_OK
    assert any(task['id'] == create_response.data['id'] for task in list_response.data['tasks'])


@hy_settings(max_examples=100, deadline=None)
@given(invalid_user_id=st.integers(min_value=100_000, max_value=999_999))
def test_invalid_user_assignment_rejection_property(invalid_user_id):
    """Property 12: Invalid assignee IDs are rejected."""
    # Property: 12
    admin_role, _ = _create_roles()
    admin_user = _create_unique_user(admin_role, 'admin_invalid_assign', 'AdminPass123')

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(admin_user))
    response = client.post(
        '/api/tasks',
        {
            'title': 'Invalid assignment',
            'description': 'Should fail',
            'assigned_to': invalid_user_id,
            'status': 'pending',
        },
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@hy_settings(max_examples=100, deadline=None)
@given(
    own_task_count=st.integers(min_value=1, max_value=5),
    other_task_count=st.integers(min_value=1, max_value=5),
)
def test_task_ownership_filtering_property(own_task_count, other_task_count):
    """Property 13: Users only retrieve tasks assigned to them."""
    # Property: 13
    admin_role, user_role = _create_roles()
    admin_user = _create_unique_user(admin_role, 'admin_ownership', 'AdminPass123')
    user_a = _create_unique_user(user_role, 'user_a', 'UserPass123')
    user_b = _create_unique_user(user_role, 'user_b', 'UserPass123')

    for index in range(own_task_count):
        Task.objects.create(
            title=f'own_{index}',
            description='own',
            assigned_to=user_a,
            created_by=admin_user,
            status='pending',
        )

    for index in range(other_task_count):
        Task.objects.create(
            title=f'other_{index}',
            description='other',
            assigned_to=user_b,
            created_by=admin_user,
            status='pending',
        )

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(user_a))
    response = client.get('/api/tasks')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == own_task_count
    assert all(task['assigned_to'] == user_a.id for task in response.data['tasks'])


@hy_settings(max_examples=100, deadline=None)
@given(status_value=st.sampled_from(['completed', 'pending']))
def test_task_status_update_authorization_property(status_value):
    """Property 14: Assignee can update, non-assignee is forbidden."""
    # Property: 14
    admin_role, user_role = _create_roles()
    admin_user = _create_unique_user(admin_role, 'admin_update_auth', 'AdminPass123')
    assignee = _create_unique_user(user_role, 'assignee_update', 'UserPass123')
    intruder = _create_unique_user(user_role, 'intruder_update', 'UserPass123')

    task = Task.objects.create(
        title='task',
        description='d',
        assigned_to=assignee,
        created_by=admin_user,
        status='pending',
    )

    assignee_client = APIClient()
    assignee_client.credentials(HTTP_AUTHORIZATION=_auth_header_for(assignee))
    assignee_response = assignee_client.put(f'/api/tasks/{task.id}', {'status': status_value}, format='json')

    intruder_client = APIClient()
    intruder_client.credentials(HTTP_AUTHORIZATION=_auth_header_for(intruder))
    intruder_response = intruder_client.put(f'/api/tasks/{task.id}', {'status': status_value}, format='json')

    assert assignee_response.status_code == status.HTTP_200_OK
    assert intruder_response.status_code == status.HTTP_403_FORBIDDEN


@hy_settings(max_examples=100, deadline=None)
@given(invalid_status=st.text(min_size=1, max_size=12).filter(lambda value: value not in {'pending', 'completed'}))
def test_task_status_transition_validity_property(invalid_status):
    """Property 15: Valid transitions accepted, invalid transitions rejected."""
    # Property: 15
    admin_role, user_role = _create_roles()
    admin_user = _create_unique_user(admin_role, 'admin_transition', 'AdminPass123')
    assignee = _create_unique_user(user_role, 'assignee_transition', 'UserPass123')

    task = Task.objects.create(
        title='transition',
        description='d',
        assigned_to=assignee,
        created_by=admin_user,
        status='pending',
    )

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(assignee))

    valid_response = client.put(f'/api/tasks/{task.id}', {'status': 'completed'}, format='json')
    invalid_response = client.put(f'/api/tasks/{task.id}', {'status': invalid_status}, format='json')
    rollback_response = client.put(f'/api/tasks/{task.id}', {'status': 'pending'}, format='json')

    assert valid_response.status_code == status.HTTP_200_OK
    assert invalid_response.status_code == status.HTTP_400_BAD_REQUEST
    assert rollback_response.status_code == status.HTTP_400_BAD_REQUEST


@hy_settings(max_examples=100, deadline=None)
@given(
    pending_count=st.integers(min_value=1, max_value=4),
    completed_count=st.integers(min_value=1, max_value=4),
)
def test_task_filtering_correctness_property(pending_count, completed_count):
    """Property 16: Combined filters return only matching tasks."""
    # Property: 16
    admin_role, user_role = _create_roles()
    admin_user = _create_unique_user(admin_role, 'admin_filter', 'AdminPass123')
    assignee = _create_unique_user(user_role, 'assignee_filter', 'UserPass123')

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

    response = client.get(f'/api/tasks?status=pending&assigned_to={assignee.id}')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == pending_count
    assert all(task['status'] == 'pending' and task['assigned_to'] == assignee.id for task in response.data['tasks'])
