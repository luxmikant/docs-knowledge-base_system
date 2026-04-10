# AI-Powered Task & Knowledge Management System - Backend

## Tech Stack

- **Framework**: Django 4.2.7 with Django REST Framework
- **Database**: PostgreSQL or PlanetScale MySQL (production), SQLite (tests/local fallback)
- **Authentication**: Local JWT and Clerk JWT
- **AI/ML**: sentence-transformers (all-MiniLM-L6-v2) + FAISS
- **Python**: 3.11+

## Project Structure

```
backend/
├── config/              # Django project configuration
│   ├── settings.py      # Main settings
│   ├── urls.py          # Root URL configuration
│   ├── wsgi.py          # WSGI configuration
│   └── asgi.py          # ASGI configuration
├── app/                 # Main application
│   ├── models.py        # Database models
│   ├── views.py         # API views
│   ├── serializers.py   # DRF serializers
│   ├── authentication.py # JWT authentication
│   ├── urls.py          # App URL routing
│   ├── utils.py         # Utility functions
│   └── services/        # Business logic services
│       ├── embedding_service.py  # AI embeddings
│       └── activity_service.py   # Activity logging
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables
└── manage.py           # Django management script
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Optional (full transformer + FAISS stack):

```bash
pip install -r requirements-ml.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and update with your settings:

```bash
cp .env.example .env
```

For local development with SQLite, you can use the default settings.

For PostgreSQL or PlanetScale, set one of these options:

- `DATABASE_URL=postgresql://<username>:<password>@<host>:5432/<database>?sslmode=require`
- `DATABASE_URL=mysql://<username>:<password>@<host>:3306/<database>`
- Or set `USE_MYSQL=True` and provide `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`

For Clerk authentication, set:

- `CLERK_AUTH_ENABLED=True`
- `CLERK_ISSUER` (for example `https://your-instance.clerk.accounts.dev`)
- `CLERK_JWT_AUDIENCE` (if your Clerk JWT template includes audience)

Optional:

- `CLERK_JWKS_URL` (auto-derived from issuer if omitted)
- `CLERK_AUTO_CREATE_USERS=True` to auto-provision local app users

### 3. Run Migrations

```bash
python manage.py migrate
```

### 4. Create Initial Roles

```bash
python manage.py shell
```

Then in the Python shell:
```python
from app.models import Role
Role.objects.create(role_name='admin')
Role.objects.create(role_name='user')
exit()
```


### 5. Create Superuser (Admin)

```bash
python manage.py createsuperuser
```

### 6. Run Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login

### Tasks
- `GET /api/tasks` - Get tasks (with filtering)
- `POST /api/tasks` - Create task (admin only)
- `POST /api/tasks/create` - Backward-compatible task creation route
- `PUT /api/tasks/{id}` - Update task status

### Documents
- `POST /api/documents` - Upload document (admin only)
- `GET /api/documents` - List documents
- `GET /api/documents/{id}` - Get document detail

### Search
- `POST /api/search` - Semantic search across documents

### Analytics
- `GET /api/analytics` - Get system analytics (admin only)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DB_NAME | Database name | taskdb |
| DB_USER | Database user | root |
| DB_PASSWORD | Database password | (empty) |
| DB_HOST | Database host | localhost |
| DB_PORT | Database port | 3306 |
| DATABASE_URL | PostgreSQL or PlanetScale connection URL | (empty) |
| DB_SSL_REQUIRED | Enable SSL options for MySQL | False |
| DB_SSL_CA | CA cert path for MySQL SSL | (empty) |
| SECRET_KEY | Django secret key | (change in production) |
| DEBUG | Debug mode | True |
| JWT_SECRET | JWT signing key | (change in production) |
| JWT_EXPIRATION_HOURS | Token expiration | 24 |
| CLERK_AUTH_ENABLED | Enable Clerk token authentication | False |
| CLERK_ISSUER | Clerk issuer URL | (empty) |
| CLERK_JWKS_URL | Clerk JWKS URL | auto from issuer |
| CLERK_JWT_AUDIENCE | Clerk JWT audience | (empty) |
| CLERK_AUTO_CREATE_USERS | Auto-create local users from Clerk | True |
| CLERK_DEFAULT_ROLE | Default role for new Clerk users | user |
| MAX_UPLOAD_SIZE_MB | Max file upload size | 10 |

## Core Dependencies

- Django==4.2.7
- djangorestframework==3.14.0
- PyJWT==2.8.0
- PyMySQL==1.1.1 (for MySQL/PlanetScale)
- psycopg2-binary==2.9.9 (for PostgreSQL)
- python-dotenv==1.0.0

## Optional AI Dependencies

- sentence-transformers==2.2.2
- faiss-cpu==1.7.4

## Testing

Run tests with:
```bash
pytest
```

## Deployment

See the main project README for deployment instructions to Render.
