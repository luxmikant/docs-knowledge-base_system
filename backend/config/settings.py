"""
Django settings for config project.
"""

import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
if 'testserver' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('testserver')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database configuration
# Use SQLite for local development, MySQL for production
database_url = os.getenv('DATABASE_URL', '').strip()
db_ssl_required = os.getenv('DB_SSL_REQUIRED', 'False') == 'True'
db_ssl_ca = os.getenv('DB_SSL_CA', '').strip()


def _mysql_options():
    options = {
        'charset': 'utf8mb4',
    }
    if db_ssl_required:
        options['ssl'] = {'ca': db_ssl_ca} if db_ssl_ca else {}
    return options

if database_url:
    parsed = urlparse(database_url)
    scheme = (parsed.scheme or '').lower()

    base_db_config = {
        'NAME': parsed.path.lstrip('/'),
        'USER': parsed.username or '',
        'PASSWORD': parsed.password or '',
        'HOST': parsed.hostname or 'localhost',
    }

    if scheme in {'postgres', 'postgresql', 'postgresql+psycopg2', 'postgresql+psycopg'}:
        options = {}
        query_params = parse_qs(parsed.query)
        sslmode = query_params.get('sslmode', [None])[0]
        if sslmode:
            options['sslmode'] = sslmode

        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                **base_db_config,
                'PORT': str(parsed.port or 5432),
                'OPTIONS': options,
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                **base_db_config,
                'PORT': str(parsed.port or 3306),
                'OPTIONS': _mysql_options(),
            }
        }
elif os.getenv('USE_MYSQL', 'False') == 'True':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DB_NAME', 'taskdb'),
            'USER': os.getenv('DB_USER', 'root'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '3306'),
            'OPTIONS': _mysql_options(),
        }
    }
else:
    # SQLite for local development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (User uploads)
MEDIA_URL = 'media/'
media_root = os.getenv('MEDIA_ROOT', '')
if media_root:
    MEDIA_ROOT = Path(media_root)
    if not MEDIA_ROOT.is_absolute():
        MEDIA_ROOT = BASE_DIR / MEDIA_ROOT
else:
    MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'app.User'

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'app.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'EXCEPTION_HANDLER': 'app.utils.custom_exception_handler',
}

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'jwt-secret-change-in-production')
JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))
ADMIN_SIGNUP_CODE = os.getenv('ADMIN_SIGNUP_CODE', '').strip()

# Search Quality
MIN_RELEVANCE_SCORE = float(os.getenv('MIN_RELEVANCE_SCORE', '0.4'))

# CORS configuration
cors_allowed_origins_raw = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').strip()
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in cors_allowed_origins_raw.split(',') if origin.strip()]

# Clerk Authentication Configuration
CLERK_AUTH_ENABLED = os.getenv('CLERK_AUTH_ENABLED', 'False') == 'True'
CLERK_ISSUER = os.getenv('CLERK_ISSUER', '').strip()
CLERK_JWKS_URL = os.getenv('CLERK_JWKS_URL', '').strip()
if CLERK_ISSUER and not CLERK_JWKS_URL:
    CLERK_JWKS_URL = f"{CLERK_ISSUER.rstrip('/')}/.well-known/jwks.json"

clerk_audience_raw = os.getenv('CLERK_JWT_AUDIENCE', '').strip()
if ',' in clerk_audience_raw:
    CLERK_JWT_AUDIENCE = [aud.strip() for aud in clerk_audience_raw.split(',') if aud.strip()]
else:
    CLERK_JWT_AUDIENCE = clerk_audience_raw or None

CLERK_AUTO_CREATE_USERS = os.getenv('CLERK_AUTO_CREATE_USERS', 'True') == 'True'
CLERK_DEFAULT_ROLE = os.getenv('CLERK_DEFAULT_ROLE', 'user')

# File Upload Settings
MAX_UPLOAD_SIZE_MB = int(os.getenv('MAX_UPLOAD_SIZE_MB', '10'))
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# FAISS Index Storage
faiss_index_path = os.getenv('FAISS_INDEX_PATH', 'data')
FAISS_INDEX_PATH = Path(faiss_index_path)
if not FAISS_INDEX_PATH.is_absolute():
    FAISS_INDEX_PATH = BASE_DIR / FAISS_INDEX_PATH
