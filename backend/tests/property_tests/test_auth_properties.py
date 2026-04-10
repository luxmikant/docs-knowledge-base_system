"""Property-based tests for authentication and RBAC."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from django.conf import settings
from hypothesis import given, settings as hy_settings, strategies as st
from rest_framework import status
from rest_framework.test import APIClient

from app.models import Role, User


pytestmark = pytest.mark.django_db


def _auth_header_for(user):
    from app.authentication import generate_jwt

    return f"Bearer {generate_jwt(user)}"


def _get_or_update_user(username, email, password, role):
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'role': role,
        },
    )
    if not created:
        user.email = email
        user.role = role
    user.set_password(password)
    user.save()
    return user


@hy_settings(max_examples=100, deadline=None)
@given(
    username=st.uuids().map(lambda value: f"user_{str(value).replace('-', '')[:12]}"),
    password=st.text(min_size=8, max_size=32, alphabet=st.characters(whitelist_categories=['Ll', 'Lu', 'Nd'])),
)
def test_jwt_token_round_trip_property(username, password):
    """Property 1: JWT token round-trip authentication."""
    # Property: 1
    user_role, _ = Role.objects.get_or_create(role_name='user')
    user = _get_or_update_user(
        username=username,
        email=f'{username}@example.com',
        password=password,
        role=user_role,
    )

    client = APIClient()
    response = client.post('/api/auth/login', {'username': username, 'password': password}, format='json')

    assert response.status_code == status.HTTP_200_OK
    token = response.data['token']
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])
    assert payload['user_id'] == user.id
    assert payload['username'] == user.username
    assert payload['role'] == user.role.role_name

    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    tasks_response = client.get('/api/tasks')
    assert tasks_response.status_code == status.HTTP_200_OK


@hy_settings(max_examples=100, deadline=None)
@given(
    invalid_password=st.text(min_size=8, max_size=32, alphabet=st.characters(whitelist_categories=['Ll', 'Lu', 'Nd'])),
    username=st.uuids().map(lambda value: f"invalid_{str(value).replace('-', '')[:12]}"),
)
def test_invalid_credentials_rejection_property(invalid_password, username):
    """Property 2: Invalid credentials are rejected."""
    # Property: 2
    user_role, _ = Role.objects.get_or_create(role_name='user')
    user = _get_or_update_user(
        username=username,
        email=f'{username}@example.com',
        password='CorrectPass123',
        role=user_role,
    )

    if invalid_password == 'CorrectPass123':
        invalid_password = 'WrongPass123'

    client = APIClient()
    response = client.post(
        '/api/auth/login',
        {'username': user.username, 'password': invalid_password},
        format='json',
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@hy_settings(max_examples=100, deadline=None)
@given(
    username=st.uuids().map(lambda value: f"exp_{str(value).replace('-', '')[:12]}"),
)
def test_token_expiration_enforcement_property(username):
    """Property 3: Expired tokens are rejected."""
    # Property: 3
    user_role, _ = Role.objects.get_or_create(role_name='user')
    user = _get_or_update_user(
        username=username,
        email=f'{username}@example.com',
        password='ValidPass123',
        role=user_role,
    )

    payload = {
        'user_id': user.id,
        'username': user.username,
        'role': user.role.role_name,
        'exp': datetime.now(UTC) - timedelta(minutes=5),
        'iat': datetime.now(UTC) - timedelta(hours=1),
    }
    expired_token = jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {expired_token}')

    response = client.get('/api/tasks')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@hy_settings(max_examples=100, deadline=None)
@given(
    role_name=st.sampled_from(['admin', 'user']),
    username=st.uuids().map(lambda value: f"rbac_{str(value).replace('-', '')[:12]}"),
)
def test_role_based_access_control_property(role_name, username):
    """Property 4: RBAC enforcement across protected endpoints."""
    # Property: 4
    role, _ = Role.objects.get_or_create(role_name=role_name)
    user = _get_or_update_user(
        username=username,
        email=f'{username}@example.com',
        password='ValidPass123',
        role=role,
    )

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(user))

    analytics_response = client.get('/api/analytics')
    if role_name == 'admin':
        assert analytics_response.status_code == status.HTTP_200_OK
    else:
        assert analytics_response.status_code == status.HTTP_403_FORBIDDEN
