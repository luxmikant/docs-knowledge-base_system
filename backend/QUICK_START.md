# Quick Start Guide - Backend Setup

## Prerequisites
- Python 3.11+ installed
- pip package manager
- (Optional) MySQL database for production

## 🚀 Quick Setup (3 steps)

### Option 1: Automated Setup (Recommended)
```bash
cd backend
python setup_complete.py
python manage.py createsuperuser
python manage.py runserver
```

### Option 2: Manual Setup
```bash
cd backend

# 1. Install dependencies
pip install -r requirements.txt

# Optional: full AI dependencies (transformer + FAISS)
pip install -r requirements-ml.txt

# 2. Setup database
python manage.py makemigrations
python manage.py migrate
python manage.py seed_roles

# 3. Create admin user and run
python manage.py createsuperuser
python manage.py runserver
```

## ✅ Verify Setup
```bash
python verify_setup.py
```

## 🔑 Default Configuration
- **Database:** SQLite (local development)
- **Debug Mode:** Enabled
- **JWT Expiration:** 24 hours
- **Max Upload Size:** 10 MB

## 📝 Environment Variables
Edit `.env` file to customize:
```env
DEBUG=True
SECRET_KEY=<your-key>
JWT_SECRET=<your-key>

# PlanetScale (recommended)
DATABASE_URL=mysql://<user>:<pass>@<host>:3306/<database>
DB_SSL_REQUIRED=True

# Clerk
CLERK_AUTH_ENABLED=True
CLERK_ISSUER=https://<your-clerk-issuer>
CLERK_JWT_AUDIENCE=<your-clerk-audience>
```

## 🧪 Test the API

### 1. Create a user (via Django shell)
```bash
python manage.py shell
```
```python
from app.models import User, Role
user_role = Role.objects.get(role_name='user')
User.objects.create_user(
    username='testuser',
    email='test@example.com',
    password='testpass123',
    role=user_role
)
exit()
```

### 2. Login and get token
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'
```

### 3. Use token to access protected endpoint
```bash
curl -X GET http://localhost:8000/api/tasks \
  -H "Authorization: Bearer <your_token_here>"
```

## 📚 Available Endpoints
- `POST /api/auth/login` - Login
- `GET /api/tasks` - Get tasks
- `POST /api/tasks` - Create task (admin)
- `PUT /api/tasks/<id>` - Update task
- `POST /api/documents` - Upload document (admin)
- `GET /api/documents` - List documents
- `GET /api/documents/<id>` - Document detail
- `POST /api/search` - Semantic search
- `GET /api/analytics` - Analytics (admin)

## 🐛 Troubleshooting

### Dependencies not installing?
```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### Database errors?
```bash
# Reset database (SQLite)
rm db.sqlite3
python manage.py migrate
python manage.py seed_roles
```

### Import errors?
```bash
# Verify Python path
python -c "import django; print(django.get_version())"
```

## 📖 More Information
- Full documentation: `README.md`
- Task completion report: `TASK1_COMPLETION.md`
- Design document: `../.kiro/specs/ai-task-knowledge-system/design.md`

## 🎯 Next Steps
1. ✅ Setup complete
2. Create test data
3. Implement document upload (Task 2)
4. Implement semantic search (Task 3)
5. Build frontend

---
Need help? Check the full README.md or run `python verify_setup.py`
