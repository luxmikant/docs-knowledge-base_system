"""
Pytest configuration and fixtures
"""
import os
import django
from django.conf import settings

# Configure Django settings before importing models
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    os.environ.setdefault('DISABLE_TRANSFORMER_MODEL', 'true')
    os.environ['DATABASE_URL'] = ''
    os.environ['USE_MYSQL'] = 'False'
    django.setup()

import pytest


@pytest.fixture
def admin_role(db):
    """Create admin role"""
    from app.models import Role
    return Role.objects.create(role_name='admin')


@pytest.fixture
def user_role(db):
    """Create user role"""
    from app.models import Role
    return Role.objects.create(role_name='user')


@pytest.fixture
def admin_user(db, admin_role):
    """Create admin user"""
    from app.models import User
    return User.objects.create_user(
        username='admin',
        email='admin@test.com',
        password='admin123',
        role=admin_role
    )


@pytest.fixture
def regular_user(db, user_role):
    """Create regular user"""
    from app.models import User
    return User.objects.create_user(
        username='user1',
        email='user1@test.com',
        password='user123',
        role=user_role
    )
