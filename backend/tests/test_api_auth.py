"""Authentication and authorization API tests."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from django.conf import settings
from rest_framework import status
from rest_framework.test import APIClient


pytestmark = pytest.mark.django_db


def _auth_header_for(user):
    from app.authentication import generate_jwt

    return f"Bearer {generate_jwt(user)}"


def test_login_with_valid_credentials_returns_token_and_user(regular_user):
    client = APIClient()

    response = client.post(
        '/api/auth/login',
        {'username': regular_user.username, 'password': 'user123'},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    assert 'token' in response.data
    assert response.data['user']['id'] == regular_user.id
    assert response.data['user']['role'] == regular_user.role.role_name


def test_signup_creates_user_and_returns_token():
    client = APIClient()

    response = client.post(
        '/api/auth/signup',
        {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'newuser123',
            'role': 'user',
        },
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert 'token' in response.data
    assert response.data['user']['username'] == 'newuser'
    assert response.data['user']['role'] == 'user'


def test_admin_signup_requires_valid_signup_code(monkeypatch):
    client = APIClient()
    monkeypatch.setattr(settings, 'ADMIN_SIGNUP_CODE', 'admin-secret')

    bad_response = client.post(
        '/api/auth/signup',
        {
            'username': 'badadmin',
            'email': 'badadmin@test.com',
            'password': 'admin1234',
            'role': 'admin',
            'admin_signup_code': 'wrong',
        },
        format='json',
    )
    ok_response = client.post(
        '/api/auth/signup',
        {
            'username': 'goodadmin',
            'email': 'goodadmin@test.com',
            'password': 'admin1234',
            'role': 'admin',
            'admin_signup_code': 'admin-secret',
        },
        format='json',
    )

    assert bad_response.status_code == status.HTTP_400_BAD_REQUEST
    assert ok_response.status_code == status.HTTP_201_CREATED
    assert ok_response.data['user']['role'] == 'admin'


def test_login_with_invalid_credentials_returns_401(regular_user):
    client = APIClient()

    response = client.post(
        '/api/auth/login',
        {'username': regular_user.username, 'password': 'wrong-password'},
        format='json',
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['error'] == 'Invalid credentials'


def test_protected_endpoint_without_token_is_rejected():
    client = APIClient()

    response = client.get('/api/tasks')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_expired_token_is_rejected(regular_user):
    client = APIClient()

    payload = {
        'user_id': regular_user.id,
        'username': regular_user.username,
        'role': regular_user.role.role_name,
        'exp': datetime.now(UTC) - timedelta(hours=1),
        'iat': datetime.now(UTC) - timedelta(hours=2),
    }
    expired_token = jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')

    client.credentials(HTTP_AUTHORIZATION=f'Bearer {expired_token}')
    response = client.get('/api/tasks')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_admin_can_access_analytics(admin_user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(admin_user))

    response = client.get('/api/analytics')

    assert response.status_code == status.HTTP_200_OK


def test_user_cannot_access_analytics(regular_user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(regular_user))

    response = client.get('/api/analytics')

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_authenticated_user_can_access_me(regular_user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(regular_user))

    response = client.get('/api/auth/me')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['username'] == regular_user.username


def test_admin_can_list_users(admin_user, regular_user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(admin_user))

    response = client.get('/api/users')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] >= 2


def test_non_admin_cannot_list_users(regular_user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=_auth_header_for(regular_user))

    response = client.get('/api/users')

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_clerk_token_fallback_authenticates(monkeypatch, regular_user):
    from app.authentication import JWTAuthentication

    client = APIClient()
    monkeypatch.setattr(settings, 'CLERK_AUTH_ENABLED', True)
    monkeypatch.setattr(JWTAuthentication, '_authenticate_with_clerk', lambda self, token: regular_user)

    client.credentials(HTTP_AUTHORIZATION='Bearer clerk-style-token')
    response = client.get('/api/tasks')

    assert response.status_code == status.HTTP_200_OK
