"""
JWT Authentication for the API
"""
import re
import jwt
from datetime import UTC, datetime, timedelta
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import Role
from .models import User


def generate_jwt(user):
    """Generate JWT token for a user"""
    now = datetime.now(UTC)
    payload = {
        'user_id': user.id,
        'username': user.username,
        'role': user.role.role_name,
        'exp': now + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
        'iat': now,
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')
    return token


class JWTAuthentication(BaseAuthentication):
    """Custom JWT authentication class"""

    _jwks_client = None
    
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization', '')

        if not auth_header:
            return None

        if not auth_header.lower().startswith('bearer '):
            return None

        token = auth_header.split(' ', 1)[1].strip()
        if not token:
            raise AuthenticationFailed('Invalid token')

        try:
            # Decode token
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])

            # Get user
            user = User.objects.get(id=payload['user_id'])

            return (user, token)

        except jwt.ExpiredSignatureError:
            clerk_user = self._authenticate_with_clerk(token)
            if clerk_user is not None:
                return (clerk_user, token)
            raise AuthenticationFailed('Token expired')
        except jwt.InvalidTokenError:
            clerk_user = self._authenticate_with_clerk(token)
            if clerk_user is not None:
                return (clerk_user, token)
            raise AuthenticationFailed('Invalid token')
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found')

    def authenticate_header(self, request):
        return 'Bearer'

    def _authenticate_with_clerk(self, token):
        """Try to authenticate Clerk-issued JWT when Clerk auth is enabled."""
        if not settings.CLERK_AUTH_ENABLED:
            return None
        if not settings.CLERK_JWKS_URL:
            return None

        try:
            if self.__class__._jwks_client is None:
                self.__class__._jwks_client = jwt.PyJWKClient(settings.CLERK_JWKS_URL)

            signing_key = self.__class__._jwks_client.get_signing_key_from_jwt(token)

            decode_options = {
                'verify_signature': True,
                'verify_aud': bool(settings.CLERK_JWT_AUDIENCE),
                'verify_iss': bool(settings.CLERK_ISSUER),
            }

            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=['RS256'],
                audience=settings.CLERK_JWT_AUDIENCE if settings.CLERK_JWT_AUDIENCE else None,
                issuer=settings.CLERK_ISSUER if settings.CLERK_ISSUER else None,
                options=decode_options,
            )
            return self._get_or_create_clerk_user(payload)
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token expired')
        except Exception:
            return None

    def _get_or_create_clerk_user(self, payload):
        """Map Clerk payload to a local user for RBAC and app ownership checks."""
        clerk_subject = payload.get('sub')
        if not clerk_subject:
            raise AuthenticationFailed('Invalid token')

        email = payload.get('email') or payload.get('email_address')
        if not email:
            email_addresses = payload.get('email_addresses')
            if isinstance(email_addresses, list) and email_addresses:
                first_email = email_addresses[0]
                if isinstance(first_email, dict):
                    email = first_email.get('email_address')

        username_claim = payload.get('username') or payload.get('preferred_username')
        base_username = self._sanitize_username(username_claim or f'clerk_{clerk_subject}')

        if email:
            existing_by_email = User.objects.filter(email=email).first()
            if existing_by_email:
                return existing_by_email

        existing_by_username = User.objects.filter(username=base_username).first()
        if existing_by_username:
            return existing_by_username

        if not settings.CLERK_AUTO_CREATE_USERS:
            raise AuthenticationFailed('No local user mapped for this Clerk account')

        role, _ = Role.objects.get_or_create(role_name=settings.CLERK_DEFAULT_ROLE)
        final_username = self._unique_username(base_username)
        final_email = self._unique_email(email or f'{base_username}@clerk.local')

        user = User(username=final_username, email=final_email, role=role)
        user.set_unusable_password()
        user.save()
        return user

    @staticmethod
    def _sanitize_username(value):
        value = re.sub(r'[^A-Za-z0-9_.-]', '_', value)
        value = value.strip('._-') or 'clerk_user'
        return value[:100]

    def _unique_username(self, base_username):
        candidate = base_username[:100]
        suffix = 1
        while User.objects.filter(username=candidate).exists():
            room = max(1, 100 - len(str(suffix)) - 1)
            candidate = f'{base_username[:room]}_{suffix}'
            suffix += 1
        return candidate

    def _unique_email(self, base_email):
        candidate = base_email
        if '@' not in candidate:
            candidate = f'{candidate}@clerk.local'

        local, domain = candidate.split('@', 1)
        suffix = 1
        while User.objects.filter(email=candidate).exists():
            candidate = f'{local}+{suffix}@{domain}'
            suffix += 1
        return candidate
