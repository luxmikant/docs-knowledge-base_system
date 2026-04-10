# AI-Powered Task & Knowledge Management System

A full-stack application that enables admins to upload documents and assign tasks, while users can search documents using AI-powered semantic search and manage their assigned tasks.

## Features

- **Role-Based Access Control**: Admin and User roles with different permissions
- **JWT Authentication**: Secure token-based authentication
- **Task Management**: Create, assign, and track tasks
- **AI-Powered Semantic Search**: Search documents using natural language queries
- **Activity Logging**: Track all user actions
- **Analytics Dashboard**: View system metrics (admin only)

## Tech Stack

### Backend
- **Framework**: Django 4.2.7 with Django REST Framework
- **Database**: MySQL (PlanetScale) / SQLite (local dev)
- **Authentication**: Local JWT and Clerk JWT
- **AI/ML**: sentence-transformers (all-MiniLM-L6-v2) + FAISS
- **Hosting**: Render

### Frontend
- **Framework**: React.js
- **State Management**: React Context API
- **Authentication UI**: Clerk
- **Hosting**: Vercel

## Project Structure

```
.
├── backend/              # Django REST API
│   ├── config/          # Django project configuration
│   ├── app/             # Main application
│   │   ├── models.py    # Database models
│   │   ├── views.py     # API views
│   │   ├── serializers.py
│   │   ├── authentication.py
│   │   └── services/    # Business logic
│   ├── tests/           # Test suite
│   └── requirements.txt
└── frontend/            # React application (to be implemented)
```

## Quick Start

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run setup script:
```bash
# On Windows
setup.bat

# On Linux/Mac
chmod +x setup.sh
./setup.sh
```

4. Create admin user:
```bash
python manage.py createsuperuser
```

5. Start development server:
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`


## API Endpoints

### Authentication
- `POST /api/auth/login` - User login, returns JWT token

### Tasks
- `GET /api/tasks` - Get tasks (filtered by user role)
- `POST /api/tasks` - Create task (admin only)
- `PUT /api/tasks/{id}` - Update task status

### Documents
- `POST /api/documents` - Upload document (admin only)
- `GET /api/documents` - List all documents
- `GET /api/documents/{id}` - Document detail

### Search
- `POST /api/search` - Semantic search

### Analytics
- `GET /api/analytics` - Get system analytics (admin only)

## Environment Variables

Create a `.env` file in the backend directory:

```env
# Database
DATABASE_URL=  # Recommended for PlanetScale
USE_MYSQL=False
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=3306
DB_SSL_REQUIRED=False

# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# JWT
JWT_SECRET=your-jwt-secret
JWT_EXPIRATION_HOURS=24

# Clerk
CLERK_AUTH_ENABLED=False
CLERK_ISSUER=
CLERK_JWKS_URL=
CLERK_JWT_AUDIENCE=
CLERK_AUTO_CREATE_USERS=True
CLERK_DEFAULT_ROLE=user

# File Upload
MAX_UPLOAD_SIZE_MB=10
```

## Database Schema

- **roles**: User roles (admin, user)
- **users**: User accounts with role assignment
- **tasks**: Task assignments and status
- **documents**: Uploaded documents with metadata
- **activity_logs**: User activity tracking

## Development

### Running Tests

```bash
cd backend
pytest
```

### Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Creating Test Data

```bash
python manage.py seed_roles
```

## Deployment

### Backend (Render)

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set environment variables
4. Deploy

### Frontend (Vercel)

1. Create a new project on Vercel
2. Connect your GitHub repository
3. Set environment variables
4. Deploy

## License

MIT License
