# Design: AI-Powered Task & Knowledge Management System

## 1. Overview

This document outlines the technical design for an AI-powered task and knowledge management system. The system enables admins to upload documents and assign tasks, while users can search documents using semantic search and manage their assigned tasks.

### 1.1 System Goals

- Provide secure, role-based access to task and document management
- Enable intelligent document search using AI embeddings
- Track user activity and provide analytics
- Maintain clean architecture with separation of concerns

### 1.2 Technology Stack

**Backend:**
- Framework: Django REST Framework (Python)
- Database: MySQL (hosted on PlanetScale)
- Authentication: JWT tokens
- Hosting: Render

**Frontend:**
- Framework: React.js
- State Management: React Context API / Redux
- Authentication: Clerk for UI, JWT for API
- Hosting: Vercel

**AI/ML:**
- Embedding Model: sentence-transformers (all-MiniLM-L6-v2)
- Vector Database: FAISS or Chroma
- Text Processing: NLTK/spaCy for preprocessing

## 2. Architecture

### 2.1 System Architecture

The system follows a three-tier architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend Layer                       │
│                    (React.js on Vercel)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Auth Module  │  │ Task Module  │  │ Search Module│     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS/REST API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend Layer                           │
│                (Django REST Framework on Render)             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Auth Service │  │ Task Service │  │ Doc Service  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Search Svc   │  │ Analytics Svc│  │ Activity Log │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│    Data Layer            │  │    AI Layer              │
│  (MySQL on PlanetScale)  │  │  (FAISS/Chroma)          │
│  ┌────────────────────┐  │  │  ┌────────────────────┐  │
│  │ Relational Data    │  │  │  │ Vector Embeddings  │  │
│  │ - Users            │  │  │  │ - Document vectors │  │
│  │ - Tasks            │  │  │  │ - Query vectors    │  │
│  │ - Documents        │  │  │  └────────────────────┘  │
│  │ - Activity Logs    │  │  │                          │
│  └────────────────────┘  │  │  ┌────────────────────┐  │
│                          │  │  │ Embedding Model    │  │
│                          │  │  │ (sentence-trans.)  │  │
│                          │  │  └────────────────────┘  │
└──────────────────────────┘  └──────────────────────────┘
```

### 2.2 Component Responsibilities

**Frontend Components:**
- Authentication: Handle login, token management, protected routes
- Task Management: Display tasks, update status, filter tasks
- Document Search: Search interface, results display
- Admin Panel: Document upload, task creation/assignment
- Analytics Dashboard: Display system metrics

**Backend Services:**
- Auth Service: JWT generation, validation, role verification
- Task Service: CRUD operations, filtering, status management
- Document Service: Upload handling, metadata storage
- Search Service: Embedding generation, vector search
- Analytics Service: Aggregate metrics, query statistics
- Activity Logger: Track and store user actions

## 3. Data Models

### 3.1 Database Schema (MySQL)

```sql
-- Roles table
CREATE TABLE roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT,
    INDEX idx_username (username),
    INDEX idx_email (email)
);

-- Documents table
CREATE TABLE documents (
    id INT PRIMARY KEY AUTO_INCREMENT,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INT NOT NULL,
    uploaded_by INT NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content_text TEXT,
    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_uploaded_by (uploaded_by),
    INDEX idx_upload_date (upload_date)
);

-- Tasks table
CREATE TABLE tasks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    assigned_to INT NOT NULL,
    created_by INT NOT NULL,
    status ENUM('pending', 'completed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_assigned_to (assigned_to),
    INDEX idx_status (status),
    INDEX idx_created_by (created_by)
);

-- Activity logs table
CREATE TABLE activity_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_action_type (action_type),
    INDEX idx_timestamp (timestamp)
);
```

### 3.2 Django Models

```python
# models.py

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class Role(models.Model):
    role_name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'roles'

class UserManager(BaseUserManager):
    def create_user(self, username, email, password, role):
        user = self.model(username=username, email=email, role=role)
        user.set_password(password)
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    role = models.ForeignKey(Role, on_delete=models.RESTRICT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    USERNAME_FIELD = 'username'
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
        ]

class Document(models.Model):
    filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.IntegerField()
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    upload_date = models.DateTimeField(auto_now_add=True)
    content_text = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'documents'
        indexes = [
            models.Index(fields=['uploaded_by']),
            models.Index(fields=['upload_date']),
        ]

class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    assigned_to = models.ForeignKey(User, related_name='assigned_tasks', on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, related_name='created_tasks', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tasks'
        indexes = [
            models.Index(fields=['assigned_to']),
            models.Index(fields=['status']),
            models.Index(fields=['created_by']),
        ]

class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=50)
    details = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'activity_logs'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['action_type']),
            models.Index(fields=['timestamp']),
        ]
```

## 4. Components and Interfaces

### 4.1 Backend API Endpoints

#### 4.1.1 Authentication Endpoints

**POST /api/auth/login**
- Description: Authenticate user and return JWT token
- Access: Public
- Request Body:
```json
{
  "username": "string",
  "password": "string"
}
```
- Response (200):
```json
{
  "token": "jwt_token_string",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "role": "admin"
  }
}
```
- Response (401):
```json
{
  "error": "Invalid credentials"
}
```

#### 4.1.2 Task Endpoints

**GET /api/tasks**
- Description: Retrieve tasks with optional filtering
- Access: Authenticated (Users see their tasks, Admins see all)
- Query Parameters:
  - `status`: Filter by status (pending/completed)
  - `assigned_to`: Filter by user ID (admin only)
- Response (200):
```json
{
  "tasks": [
    {
      "id": 1,
      "title": "Review documentation",
      "description": "Review the uploaded docs",
      "assigned_to": 5,
      "created_by": 1,
      "status": "pending",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "count": 1
}
```

**POST /api/tasks**
- Description: Create new task
- Access: Admin only
- Request Body:
```json
{
  "title": "string",
  "description": "string",
  "assigned_to": 5
}
```
- Response (201):
```json
{
  "id": 1,
  "title": "string",
  "description": "string",
  "assigned_to": 5,
  "created_by": 1,
  "status": "pending",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**PUT /api/tasks/{id}**
- Description: Update task status
- Access: Authenticated (Users can update their tasks)
- Request Body:
```json
{
  "status": "completed"
}
```
- Response (200):
```json
{
  "id": 1,
  "status": "completed",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

#### 4.1.3 Document Endpoints

**POST /api/documents**
- Description: Upload document
- Access: Admin only
- Request: multipart/form-data
  - `file`: File upload (.txt)
- Response (201):
```json
{
  "id": 1,
  "filename": "guide.txt",
  "file_size": 2048,
  "uploaded_by": 1,
  "upload_date": "2024-01-15T10:30:00Z"
}
```

**GET /api/documents**
- Description: List all documents
- Access: Authenticated
- Response (200):
```json
{
  "documents": [
    {
      "id": 1,
      "filename": "guide.txt",
      "file_size": 2048,
      "uploaded_by": 1,
      "upload_date": "2024-01-15T10:30:00Z"
    }
  ],
  "count": 1
}
```

**GET /api/documents/{id}**
- Description: Retrieve document details
- Access: Authenticated
- Response (200):
```json
{
  "id": 1,
  "filename": "guide.txt",
  "file_size": 2048,
  "uploaded_by": 1,
  "upload_date": "2024-01-15T10:30:00Z",
  "content_preview": "First 500 characters..."
}
```

#### 4.1.4 Search Endpoint

**POST /api/search**
- Description: Semantic search across documents
- Access: Authenticated
- Request Body:
```json
{
  "query": "How do I configure authentication?",
  "top_k": 5
}
```
- Response (200):
```json
{
  "results": [
    {
      "document_id": 1,
      "filename": "auth_guide.txt",
      "relevance_score": 0.89,
      "content_snippet": "...authentication configuration steps..."
    }
  ],
  "query": "How do I configure authentication?",
  "count": 1
}
```

#### 4.1.5 Analytics Endpoint

**GET /api/analytics**
- Description: Retrieve system analytics
- Access: Admin only
- Response (200):
```json
{
  "tasks": {
    "total": 50,
    "completed": 30,
    "pending": 20
  },
  "searches": {
    "total_queries": 150,
    "top_queries": [
      {"query": "authentication", "count": 25},
      {"query": "database setup", "count": 18}
    ]
  },
  "documents": {
    "total": 10,
    "total_size_mb": 5.2
  }
}
```

### 4.2 Frontend Component Architecture

```
src/
├── components/
│   ├── auth/
│   │   ├── LoginForm.jsx
│   │   ├── ProtectedRoute.jsx
│   │   └── AuthContext.jsx
│   ├── tasks/
│   │   ├── TaskList.jsx
│   │   ├── TaskItem.jsx
│   │   ├── TaskFilter.jsx
│   │   └── CreateTaskForm.jsx (Admin)
│   ├── documents/
│   │   ├── DocumentList.jsx
│   │   ├── DocumentUpload.jsx (Admin)
│   │   └── DocumentItem.jsx
│   ├── search/
│   │   ├── SearchBar.jsx
│   │   ├── SearchResults.jsx
│   │   └── ResultItem.jsx
│   ├── analytics/
│   │   ├── AnalyticsDashboard.jsx (Admin)
│   │   └── MetricCard.jsx
│   └── common/
│       ├── Header.jsx
│       ├── Sidebar.jsx
│       └── LoadingSpinner.jsx
├── services/
│   ├── api.js
│   ├── authService.js
│   ├── taskService.js
│   ├── documentService.js
│   └── searchService.js
├── hooks/
│   ├── useAuth.js
│   ├── useTasks.js
│   └── useSearch.js
├── utils/
│   ├── tokenManager.js
│   └── validators.js
└── App.jsx
```

### 4.3 Key Frontend Components

**AuthContext.jsx**
```javascript
// Manages authentication state globally
- Stores JWT token
- Provides login/logout functions
- Exposes user role information
- Handles token refresh
```

**ProtectedRoute.jsx**
```javascript
// Route guard component
- Checks authentication status
- Validates user role for admin routes
- Redirects to login if unauthorized
```

**TaskList.jsx**
```javascript
// Displays filtered task list
- Fetches tasks based on filters
- Shows status badges
- Allows status updates
- Supports pagination
```

**SearchBar.jsx**
```javascript
// Semantic search interface
- Input for natural language queries
- Debounced search execution
- Loading states
- Error handling
```

## 5. AI/ML Pipeline Design

### 5.1 Embedding Generation Pipeline

```
Document Upload → Text Extraction → Preprocessing → Embedding → Vector Storage
```

**Step 1: Text Extraction**
- Read .txt file content
- Store raw text in MySQL `documents.content_text`

**Step 2: Text Preprocessing**
- Remove special characters
- Normalize whitespace
- Split into chunks (512 tokens max)
- Preserve semantic boundaries

**Step 3: Embedding Generation**
- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Input: Text chunks
- Output: 384-dimensional vectors
- Batch processing for efficiency

**Step 4: Vector Storage**
- Store in FAISS index or Chroma collection
- Maintain document_id → vector mapping
- Enable efficient similarity search

### 5.2 Search Pipeline

```
User Query → Query Embedding → Vector Search → Ranking → Results
```

**Step 1: Query Embedding**
- Convert query to 384-dim vector using same model
- Apply same preprocessing as documents

**Step 2: Vector Search**
- Perform cosine similarity search in FAISS/Chroma
- Retrieve top-k most similar vectors
- Default k=5, configurable

**Step 3: Ranking**
- Sort by similarity score (0-1 range)
- Filter results below threshold (e.g., 0.3)
- Retrieve document metadata from MySQL

**Step 4: Results Formatting**
- Include document ID, filename, score
- Extract relevant snippet (context window)
- Return formatted JSON response

### 5.3 Implementation Details

**Embedding Service (Python)**
```python
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = 384
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine
        self.doc_id_map = {}
    
    def generate_embedding(self, text):
        """Generate embedding for text"""
        return self.model.encode(text, normalize_embeddings=True)
    
    def add_document(self, doc_id, text):
        """Add document to vector index"""
        embedding = self.generate_embedding(text)
        self.index.add(np.array([embedding]))
        idx = self.index.ntotal - 1
        self.doc_id_map[idx] = doc_id
    
    def search(self, query, top_k=5):
        """Search for similar documents"""
        query_embedding = self.generate_embedding(query)
        scores, indices = self.index.search(np.array([query_embedding]), top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx in self.doc_id_map:
                results.append({
                    'doc_id': self.doc_id_map[idx],
                    'score': float(score)
                })
        return results
```

### 5.4 Vector Database Choice

**Option 1: FAISS (Recommended for MVP)**
- Pros: Fast, in-memory, no external dependencies
- Cons: Not persistent by default (need to save/load index)
- Use case: Small to medium document collections (<10k docs)

**Option 2: Chroma**
- Pros: Persistent storage, built-in metadata filtering
- Cons: Additional dependency, slightly slower
- Use case: Larger collections, need persistence

**MVP Recommendation:** Start with FAISS, save index to disk periodically

## 6. Authentication Flow

### 6.1 Login Flow

```
User → Frontend → POST /api/auth/login → Backend
                                            ↓
                                    Validate credentials
                                            ↓
                                    Generate JWT token
                                            ↓
                                    Log activity
                                            ↓
Frontend ← Return token + user info ← Backend
    ↓
Store token in localStorage
    ↓
Set Authorization header for future requests
```

### 6.2 JWT Token Structure

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "user_id": 1,
    "username": "john_doe",
    "role": "admin",
    "exp": 1705334400,
    "iat": 1705248000
  }
}
```

### 6.3 Authorization Middleware

```python
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import jwt

class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return None
        
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user = User.objects.get(id=payload['user_id'])
            return (user, token)
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found')

def admin_required(view_func):
    """Decorator to require admin role"""
    def wrapper(request, *args, **kwargs):
        if request.user.role.role_name != 'admin':
            return JsonResponse({'error': 'Admin access required'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper
```

### 6.4 Frontend Token Management

```javascript
// tokenManager.js
export const TokenManager = {
  setToken(token) {
    localStorage.setItem('jwt_token', token);
  },
  
  getToken() {
    return localStorage.getItem('jwt_token');
  },
  
  removeToken() {
    localStorage.removeItem('jwt_token');
  },
  
  isTokenExpired() {
    const token = this.getToken();
    if (!token) return true;
    
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp * 1000 < Date.now();
  }
};

// API service with automatic token injection
export const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
});

apiClient.interceptors.request.use(config => {
  const token = TokenManager.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```


## 7. Error Handling

### 7.1 Backend Error Handling Strategy

**Error Response Format:**
```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {}
}
```

**HTTP Status Codes:**
- 200: Success
- 201: Created
- 400: Bad Request (validation errors)
- 401: Unauthorized (missing/invalid token)
- 403: Forbidden (insufficient permissions)
- 404: Not Found
- 500: Internal Server Error

**Error Categories:**

1. **Authentication Errors**
   - Invalid credentials → 401
   - Token expired → 401
   - Missing token → 401

2. **Authorization Errors**
   - Insufficient permissions → 403
   - Role mismatch → 403

3. **Validation Errors**
   - Missing required fields → 400
   - Invalid data format → 400
   - File type not supported → 400

4. **Resource Errors**
   - Document not found → 404
   - Task not found → 404
   - User not found → 404

5. **Business Logic Errors**
   - Cannot assign task to non-existent user → 400
   - Cannot update task not assigned to you → 403

**Exception Handler:**
```python
from rest_framework.views import exception_handler
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if response is not None:
        custom_response = {
            'error': str(exc),
            'code': exc.__class__.__name__,
            'status': response.status_code
        }
        response.data = custom_response
    
    return response
```

### 7.2 Frontend Error Handling

**Error Display Strategy:**
- Toast notifications for transient errors
- Inline validation messages for forms
- Error boundaries for component crashes
- Retry mechanisms for network failures

**Error Handling Hook:**
```javascript
export const useErrorHandler = () => {
  const [error, setError] = useState(null);
  
  const handleError = (error) => {
    if (error.response) {
      // Server responded with error
      const message = error.response.data.error || 'An error occurred';
      setError(message);
      
      if (error.response.status === 401) {
        // Token expired, redirect to login
        TokenManager.removeToken();
        window.location.href = '/login';
      }
    } else if (error.request) {
      // Network error
      setError('Network error. Please check your connection.');
    } else {
      setError('An unexpected error occurred.');
    }
  };
  
  return { error, handleError, clearError: () => setError(null) };
};
```

### 7.3 Activity Logging for Errors

All errors should be logged to activity_logs with action_type='error':
```python
def log_error(user_id, error_type, details):
    ActivityLog.objects.create(
        user_id=user_id,
        action_type='error',
        details=json.dumps({
            'error_type': error_type,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
    )
```

## 8. Testing Strategy

### 8.1 Backend Testing

**Unit Tests:**
- Test individual service methods
- Mock database calls
- Test authentication logic
- Test embedding generation
- Test search algorithms

**Integration Tests:**
- Test API endpoints end-to-end
- Test database operations
- Test file upload flow
- Test search pipeline

**Test Framework:** pytest + Django TestCase

**Example Test:**
```python
from django.test import TestCase
from rest_framework.test import APIClient

class TaskAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='pass123',
            role=Role.objects.get(role_name='admin')
        )
        self.token = generate_jwt(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_create_task_as_admin(self):
        response = self.client.post('/api/tasks', {
            'title': 'Test Task',
            'description': 'Test Description',
            'assigned_to': self.admin.id
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['title'], 'Test Task')
    
    def test_filter_tasks_by_status(self):
        # Create tasks with different statuses
        Task.objects.create(title='Task 1', status='pending', assigned_to=self.admin, created_by=self.admin)
        Task.objects.create(title='Task 2', status='completed', assigned_to=self.admin, created_by=self.admin)
        
        response = self.client.get('/api/tasks?status=pending')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['tasks']), 1)
        self.assertEqual(response.data['tasks'][0]['status'], 'pending')
```

### 8.2 Frontend Testing

**Unit Tests:**
- Test component rendering
- Test user interactions
- Test state management
- Test utility functions

**Integration Tests:**
- Test API service calls
- Test authentication flow
- Test form submissions

**Test Framework:** Jest + React Testing Library

**Example Test:**
```javascript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { TaskList } from './TaskList';
import { taskService } from '../../services/taskService';

jest.mock('../../services/taskService');

describe('TaskList', () => {
  it('displays tasks after loading', async () => {
    const mockTasks = [
      { id: 1, title: 'Task 1', status: 'pending' },
      { id: 2, title: 'Task 2', status: 'completed' }
    ];
    
    taskService.getTasks.mockResolvedValue({ tasks: mockTasks });
    
    render(<TaskList />);
    
    await waitFor(() => {
      expect(screen.getByText('Task 1')).toBeInTheDocument();
      expect(screen.getByText('Task 2')).toBeInTheDocument();
    });
  });
  
  it('filters tasks by status', async () => {
    render(<TaskList />);
    
    const filterSelect = screen.getByLabelText('Status');
    fireEvent.change(filterSelect, { target: { value: 'completed' } });
    
    await waitFor(() => {
      expect(taskService.getTasks).toHaveBeenCalledWith({ status: 'completed' });
    });
  });
});
```

### 8.3 AI/ML Testing

**Embedding Quality Tests:**
- Test embedding generation for various text lengths
- Test similarity scores for known similar/dissimilar texts
- Test edge cases (empty text, special characters)

**Search Quality Tests:**
- Test search returns relevant results
- Test ranking order is correct
- Test query preprocessing

**Example Test:**
```python
class EmbeddingServiceTest(TestCase):
    def setUp(self):
        self.service = EmbeddingService()
    
    def test_similar_texts_have_high_similarity(self):
        text1 = "How to configure authentication"
        text2 = "Authentication configuration guide"
        
        emb1 = self.service.generate_embedding(text1)
        emb2 = self.service.generate_embedding(text2)
        
        similarity = np.dot(emb1, emb2)
        self.assertGreater(similarity, 0.7)
    
    def test_dissimilar_texts_have_low_similarity(self):
        text1 = "How to configure authentication"
        text2 = "Recipe for chocolate cake"
        
        emb1 = self.service.generate_embedding(text1)
        emb2 = self.service.generate_embedding(text2)
        
        similarity = np.dot(emb1, emb2)
        self.assertLess(similarity, 0.3)
```

## 9. Deployment Architecture

### 9.1 Infrastructure Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Users                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Vercel (Frontend)                         │
│  - React.js application                                      │
│  - Static asset hosting                                      │
│  - CDN distribution                                          │
│  - Environment variables for API URL                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Render (Backend)                          │
│  - Django REST Framework                                     │
│  - Gunicorn WSGI server                                      │
│  - Environment variables (DB, JWT secret)                    │
│  - File storage for documents                                │
│  - FAISS index persistence                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                PlanetScale (MySQL Database)                  │
│  - Managed MySQL hosting                                     │
│  - Automatic backups                                         │
│  - Connection pooling                                        │
└─────────────────────────────────────────────────────────────┘
```

### 9.2 Backend Deployment (Render)

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download sentence-transformers model
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run migrations and start server
CMD python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

**requirements.txt:**
```
Django==4.2.7
djangorestframework==3.14.0
PyJWT==2.8.0
mysqlclient==2.2.0
sentence-transformers==2.2.2
faiss-cpu==1.7.4
gunicorn==21.2.0
python-dotenv==1.0.0
```

**Environment Variables (Render):**
```
DATABASE_URL=mysql://user:pass@host:port/dbname
SECRET_KEY=your-secret-key
JWT_SECRET=your-jwt-secret
ALLOWED_HOSTS=your-app.onrender.com
DEBUG=False
```

### 9.3 Frontend Deployment (Vercel)

**vercel.json:**
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "build",
  "devCommand": "npm start",
  "env": {
    "REACT_APP_API_URL": "@api_url"
  }
}
```

**Environment Variables (Vercel):**
```
REACT_APP_API_URL=https://your-backend.onrender.com/api
REACT_APP_CLERK_PUBLISHABLE_KEY=your-clerk-key
```

### 9.4 Database Setup (PlanetScale)

**Initial Setup:**
1. Create PlanetScale database
2. Get connection string
3. Run migrations from local environment:
```bash
python manage.py migrate --database=planetscale
```

**Connection Configuration:**
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'ssl': {'ca': '/path/to/ca-cert.pem'}
        }
    }
}
```

### 9.5 File Storage Strategy

**Document Storage:**
- Store uploaded files in Render's persistent disk
- Path: `/app/media/documents/`
- Backup strategy: Periodic sync to cloud storage (S3/GCS)

**FAISS Index Storage:**
- Save index to disk after each update
- Path: `/app/data/faiss_index.bin`
- Load on application startup

```python
# Save index
import pickle

def save_index(embedding_service, path='/app/data/'):
    faiss.write_index(embedding_service.index, f'{path}faiss_index.bin')
    with open(f'{path}doc_id_map.pkl', 'wb') as f:
        pickle.dump(embedding_service.doc_id_map, f)

# Load index
def load_index(embedding_service, path='/app/data/'):
    if os.path.exists(f'{path}faiss_index.bin'):
        embedding_service.index = faiss.read_index(f'{path}faiss_index.bin')
        with open(f'{path}doc_id_map.pkl', 'rb') as f:
            embedding_service.doc_id_map = pickle.load(f)
```

### 9.6 CI/CD Pipeline

**GitHub Actions Workflow:**
```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest
  
  deploy-backend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Render
        run: curl ${{ secrets.RENDER_DEPLOY_HOOK }}
  
  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
```

## 10. Security Considerations

### 10.1 Authentication Security

- JWT tokens expire after 24 hours
- Passwords hashed using Django's PBKDF2 algorithm
- HTTPS enforced for all API calls
- Token stored in localStorage (consider httpOnly cookies for production)

### 10.2 Authorization Security

- Role validation on every protected endpoint
- Users can only access their own tasks
- Admins have full access but actions are logged
- SQL injection prevention via ORM

### 10.3 File Upload Security

- Validate file extensions (.txt only)
- Limit file size (e.g., 10MB max)
- Sanitize filenames
- Store files outside web root
- Scan for malicious content (optional)

```python
def validate_file_upload(file):
    # Check extension
    if not file.name.endswith('.txt'):
        raise ValidationError('Only .txt files allowed')
    
    # Check size (10MB)
    if file.size > 10 * 1024 * 1024:
        raise ValidationError('File too large (max 10MB)')
    
    # Sanitize filename
    filename = secure_filename(file.name)
    return filename
```

### 10.4 API Rate Limiting

Implement rate limiting to prevent abuse:
```python
from rest_framework.throttling import UserRateThrottle

class SearchRateThrottle(UserRateThrottle):
    rate = '100/hour'  # 100 searches per hour per user
```

### 10.5 Data Privacy

- Activity logs contain user actions but not sensitive data
- Document content not exposed in list endpoints
- Search queries logged for analytics but anonymizable
- GDPR compliance considerations for user data

## 11. Performance Optimization

### 11.1 Database Optimization

- Indexes on frequently queried fields (user_id, status, timestamp)
- Connection pooling for database connections
- Query optimization using Django ORM select_related/prefetch_related
- Pagination for large result sets

### 11.2 Search Performance

- Batch embedding generation for multiple documents
- FAISS index optimization (use IndexIVFFlat for large collections)
- Cache frequently searched queries
- Async processing for document uploads

### 11.3 Frontend Performance

- Code splitting for route-based lazy loading
- Memoization of expensive computations
- Debouncing search input
- Virtual scrolling for large lists
- Image/asset optimization

### 11.4 Caching Strategy

**Backend Caching:**
```python
from django.core.cache import cache

def get_analytics():
    cached = cache.get('analytics_data')
    if cached:
        return cached
    
    data = compute_analytics()
    cache.set('analytics_data', data, timeout=300)  # 5 minutes
    return data
```

**Frontend Caching:**
- React Query for API response caching
- Service Worker for offline support (optional)

## 12. Monitoring and Logging

### 12.1 Application Logging

**Log Levels:**
- INFO: Normal operations (login, task creation)
- WARNING: Unusual but handled events
- ERROR: Errors that need attention
- CRITICAL: System failures

**Logging Configuration:**
```python
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': '/app/logs/django.log',
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
        },
        'app': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
        },
    },
}
```

### 12.2 Performance Monitoring

- Track API response times
- Monitor database query performance
- Track search latency
- Monitor embedding generation time

### 12.3 Error Tracking

- Integrate Sentry for error tracking (optional)
- Log all 500 errors with stack traces
- Alert on critical errors

## 13. Future Enhancements

### 13.1 Phase 2 Features

- PDF document support
- Multi-file upload
- Document versioning
- Task comments and attachments
- Email notifications
- Real-time updates via WebSockets

### 13.2 Scalability Improvements

- Migrate to Chroma for better vector storage
- Implement Redis for caching
- Add Celery for async task processing
- Implement full-text search alongside semantic search
- Add Elasticsearch for advanced search features

### 13.3 AI Enhancements

- Fine-tune embedding model on domain-specific data
- Implement query expansion
- Add question-answering capabilities
- Implement document summarization
- Add relevance feedback mechanism

## 14. Development Workflow

### 14.1 Local Development Setup

**Backend:**
```bash
# Clone repository
git clone <repo-url>
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your local settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load initial data (roles)
python manage.py loaddata initial_data.json

# Run development server
python manage.py runserver
```

**Frontend:**
```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your local API URL

# Run development server
npm start
```

### 14.2 Database Seeding

```python
# management/commands/seed_data.py
from django.core.management.base import BaseCommand
from app.models import Role, User, Task, Document

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # Create roles
        admin_role = Role.objects.create(role_name='admin')
        user_role = Role.objects.create(role_name='user')
        
        # Create users
        admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role=admin_role
        )
        
        user = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='user123',
            role=user_role
        )
        
        self.stdout.write(self.style.SUCCESS('Data seeded successfully'))
```

### 14.3 Git Workflow

- Main branch: `main` (production)
- Development branch: `develop`
- Feature branches: `feature/feature-name`
- Bugfix branches: `bugfix/bug-name`

**Branch Strategy:**
1. Create feature branch from `develop`
2. Implement feature with tests
3. Create pull request to `develop`
4. Code review and approval
5. Merge to `develop`
6. Periodic releases from `develop` to `main`

## 15. API Documentation

### 15.1 OpenAPI/Swagger Integration

```python
# settings.py
INSTALLED_APPS = [
    ...
    'drf_yasg',
]

# urls.py
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Task & Knowledge Management API",
        default_version='v1',
        description="API for AI-powered task and knowledge management",
    ),
    public=True,
)

urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0)),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0)),
]
```

### 15.2 API Versioning

- Current version: v1
- URL structure: `/api/v1/endpoint`
- Version in Accept header: `Accept: application/vnd.api+json; version=1`

## 16. Conclusion

This design document provides a comprehensive blueprint for building the AI-Powered Task & Knowledge Management System. The architecture emphasizes:

- **Scalability**: Modular design allows for easy expansion
- **Security**: JWT authentication, RBAC, and proper error handling
- **Performance**: Optimized database queries, caching, and efficient vector search
- **Maintainability**: Clean code structure, comprehensive testing, and documentation
- **User Experience**: Intuitive interfaces for both admins and users

The system leverages modern technologies (Django REST Framework, React, sentence-transformers, FAISS) to deliver a robust MVP that can be extended with additional features in future phases.


## 17. Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: JWT Token Authentication Round-Trip

*For any* valid user credentials, logging in should generate a JWT token that, when decoded, contains the correct user information (user_id, username, role) and can be used to authenticate subsequent requests.

**Validates: Requirements 3.1.1**

### Property 2: Invalid Credentials Rejection

*For any* invalid credential combination (wrong password, non-existent username, malformed input), the authentication system SHALL reject the login attempt and return a 401 Unauthorized response.

**Validates: Requirements 3.1.1**

### Property 3: Token Expiration Enforcement

*For any* JWT token with an expiration timestamp in the past, requests to protected endpoints SHALL be rejected with a 401 Unauthorized response.

**Validates: Requirements 3.1.1**

### Property 4: Role-Based Access Control

*For any* API endpoint and user role combination, the system SHALL enforce access control such that:
- Admin role can access all endpoints
- User role can only access user-permitted endpoints
- Unauthorized role access returns 403 Forbidden

**Validates: Requirements 3.1.2**

### Property 5: Document Metadata Persistence

*For any* uploaded document, the system SHALL store complete metadata (filename, file_path, file_size, uploaded_by, upload_date) in the database, and this metadata SHALL be retrievable by document ID.

**Validates: Requirements 3.2.1, 3.2.2**

### Property 6: Document Content Extraction

*For any* uploaded .txt document, the system SHALL successfully extract the text content and store it in the content_text field, preserving the original text accurately.

**Validates: Requirements 3.2.1**

### Property 7: Embedding Generation Consistency

*For any* text input, the embedding generation system SHALL produce a 384-dimensional vector, and generating embeddings for the same text multiple times SHALL produce identical or nearly identical vectors (cosine similarity > 0.99).

**Validates: Requirements 3.3.1**

### Property 8: Embedding Storage and Retrieval

*For any* document embedding generated and stored in the vector database, the embedding SHALL be retrievable and usable for similarity search operations.

**Validates: Requirements 3.3.1**

### Property 9: Search Result Cardinality

*For any* search query with parameter top_k=N, the system SHALL return at most N results, and if fewer than N documents exist in the database, SHALL return all available documents.

**Validates: Requirements 3.3.2**

### Property 10: Search Result Completeness

*For any* search result returned, the result SHALL include all required fields: document_id, filename, relevance_score, and content_snippet.

**Validates: Requirements 3.3.2**

### Property 11: Task Creation and Assignment

*For any* valid task data (title, description, assigned_to with valid user_id), an admin SHALL be able to create the task, and the assigned user SHALL be able to retrieve that task through the API.

**Validates: Requirements 3.4.1, 3.4.2**

### Property 12: Invalid User Assignment Rejection

*For any* task creation attempt with an invalid or non-existent assigned_to user_id, the system SHALL reject the request and return an appropriate error response.

**Validates: Requirements 3.4.2**

### Property 13: Task Ownership Filtering

*For any* user, retrieving their tasks SHALL return all and only the tasks assigned to that user, excluding tasks assigned to other users.

**Validates: Requirements 3.4.2**

### Property 14: Task Status Update Authorization

*For any* task, the assigned user SHALL be able to update the task status, the status change SHALL be persisted in the database, and users SHALL NOT be able to update tasks assigned to other users (403 Forbidden).

**Validates: Requirements 3.4.3**

### Property 15: Task Status Transition Validity

*For any* task status update from pending to completed, the system SHALL accept the transition and persist the new status. Invalid status transitions SHALL be rejected.

**Validates: Requirements 3.4.3**

### Property 16: Task Filtering Correctness

*For any* combination of filter parameters (status, assigned_to), the GET /tasks endpoint SHALL return only tasks that match ALL specified filter criteria, and SHALL return an error for invalid filter values.

**Validates: Requirements 3.4.4**

### Property 17: Activity Logging Completeness

*For any* key user action (login, document upload, task creation, task status update, search query), the system SHALL create an activity log entry containing user_id, action_type, relevant details, and timestamp.

**Validates: Requirements 3.2.1, 3.3.2, 3.4.1, 3.4.3, 3.5.1**

### Property 18: Analytics Count Accuracy

*For any* state of the task database, the analytics endpoint SHALL return accurate counts where:
- total tasks = completed tasks + pending tasks
- Each count matches the actual number of tasks in that state

**Validates: Requirements 3.6.1**

### Property 19: Search Query Frequency Tracking

*For any* set of search queries performed, the analytics endpoint SHALL accurately identify and rank the most frequent queries, with counts matching the actual number of times each query was executed.

**Validates: Requirements 3.6.2**

### Property 20: Semantic Search Relevance Ordering

*For any* search query, the returned results SHALL be ordered by relevance score in descending order (highest relevance first), and semantically similar documents SHALL have higher relevance scores than dissimilar documents.

**Validates: Requirements 3.3.2**



## 18. Property-Based Testing Strategy

### 18.1 Testing Framework Selection

**Backend Property Testing:**
- Framework: **Hypothesis** (Python property-based testing library)
- Integration with pytest
- Minimum 100 iterations per property test

**Installation:**
```bash
pip install hypothesis
```

### 18.2 Property Test Implementation Guidelines

Each correctness property from Section 17 MUST be implemented as a property-based test with the following requirements:

1. **Minimum 100 iterations** per test (configured via `@settings(max_examples=100)`)
2. **Tag format**: Each test must include a comment referencing the design property
   ```python
   # Feature: ai-task-knowledge-system, Property 1: JWT Token Authentication Round-Trip
   ```
3. **Generator strategy**: Use Hypothesis strategies to generate diverse test inputs
4. **Assertion clarity**: Each test must clearly assert the property being validated

### 18.3 Example Property Test Implementation

**Property 1: JWT Token Authentication Round-Trip**
```python
from hypothesis import given, settings, strategies as st
from hypothesis.extra.django import TestCase
import jwt
from datetime import datetime, timedelta

class AuthenticationPropertyTests(TestCase):
    
    @given(
        username=st.text(min_size=3, max_size=50, alphabet=st.characters(blacklist_characters=['\x00'])),
        password=st.text(min_size=8, max_size=100),
        email=st.emails()
    )
    @settings(max_examples=100)
    def test_jwt_token_round_trip(self, username, password, email):
        """
        Feature: ai-task-knowledge-system, Property 1: JWT Token Authentication Round-Trip
        
        For any valid user credentials, logging in should generate a JWT token that,
        when decoded, contains the correct user information.
        """
        # Create user with generated credentials
        role = Role.objects.get(role_name='user')
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role
        )
        
        # Login and get token
        response = self.client.post('/api/auth/login', {
            'username': username,
            'password': password
        })
        
        self.assertEqual(response.status_code, 200)
        token = response.data['token']
        
        # Decode token and verify payload
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        
        self.assertEqual(payload['user_id'], user.id)
        self.assertEqual(payload['username'], username)
        self.assertEqual(payload['role'], 'user')
        
        # Use token for authenticated request
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/tasks')
        self.assertEqual(response.status_code, 200)
```

**Property 16: Task Filtering Correctness**
```python
from hypothesis import given, settings, strategies as st

class TaskFilteringPropertyTests(TestCase):
    
    @given(
        num_pending=st.integers(min_value=0, max_value=20),
        num_completed=st.integers(min_value=0, max_value=20),
        filter_status=st.sampled_from(['pending', 'completed', None])
    )
    @settings(max_examples=100)
    def test_task_status_filtering(self, num_pending, num_completed, filter_status):
        """
        Feature: ai-task-knowledge-system, Property 16: Task Filtering Correctness
        
        For any combination of filter parameters, the GET /tasks endpoint SHALL
        return only tasks that match ALL specified filter criteria.
        """
        # Create test user
        user = self.create_test_user()
        self.client.force_authenticate(user=user)
        
        # Create tasks with different statuses
        for _ in range(num_pending):
            Task.objects.create(
                title=f'Task {_}',
                assigned_to=user,
                created_by=user,
                status='pending'
            )
        
        for _ in range(num_completed):
            Task.objects.create(
                title=f'Task {_}',
                assigned_to=user,
                created_by=user,
                status='completed'
            )
        
        # Apply filter
        if filter_status:
            response = self.client.get(f'/api/tasks?status={filter_status}')
        else:
            response = self.client.get('/api/tasks')
        
        self.assertEqual(response.status_code, 200)
        tasks = response.data['tasks']
        
        # Verify filtering correctness
        if filter_status == 'pending':
            self.assertEqual(len(tasks), num_pending)
            self.assertTrue(all(t['status'] == 'pending' for t in tasks))
        elif filter_status == 'completed':
            self.assertEqual(len(tasks), num_completed)
            self.assertTrue(all(t['status'] == 'completed' for t in tasks))
        else:
            self.assertEqual(len(tasks), num_pending + num_completed)
```

**Property 7: Embedding Generation Consistency**
```python
from hypothesis import given, settings, strategies as st
import numpy as np

class EmbeddingPropertyTests(TestCase):
    
    @given(
        text=st.text(min_size=10, max_size=1000)
    )
    @settings(max_examples=100)
    def test_embedding_generation_consistency(self, text):
        """
        Feature: ai-task-knowledge-system, Property 7: Embedding Generation Consistency
        
        For any text input, generating embeddings for the same text multiple times
        SHALL produce identical or nearly identical vectors (cosine similarity > 0.99).
        """
        embedding_service = EmbeddingService()
        
        # Generate embedding twice
        emb1 = embedding_service.generate_embedding(text)
        emb2 = embedding_service.generate_embedding(text)
        
        # Verify dimension
        self.assertEqual(len(emb1), 384)
        self.assertEqual(len(emb2), 384)
        
        # Verify consistency (cosine similarity)
        similarity = np.dot(emb1, emb2)
        self.assertGreater(similarity, 0.99)
```

### 18.4 Hypothesis Strategy Patterns

**User Data Generation:**
```python
user_strategy = st.builds(
    dict,
    username=st.text(min_size=3, max_size=50),
    email=st.emails(),
    password=st.text(min_size=8, max_size=100)
)
```

**Task Data Generation:**
```python
task_strategy = st.builds(
    dict,
    title=st.text(min_size=1, max_size=255),
    description=st.text(max_size=1000),
    status=st.sampled_from(['pending', 'completed'])
)
```

**Search Query Generation:**
```python
search_query_strategy = st.text(
    min_size=3,
    max_size=200,
    alphabet=st.characters(whitelist_categories=['L', 'N', 'P', 'Z'])
)
```

### 18.5 Property Test Coverage Requirements

Each property from Section 17 MUST have at least one corresponding property-based test:

| Property | Test Class | Test Method |
|----------|------------|-------------|
| Property 1 | AuthenticationPropertyTests | test_jwt_token_round_trip |
| Property 2 | AuthenticationPropertyTests | test_invalid_credentials_rejection |
| Property 3 | AuthenticationPropertyTests | test_token_expiration_enforcement |
| Property 4 | AuthorizationPropertyTests | test_role_based_access_control |
| Property 5 | DocumentPropertyTests | test_document_metadata_persistence |
| Property 6 | DocumentPropertyTests | test_document_content_extraction |
| Property 7 | EmbeddingPropertyTests | test_embedding_generation_consistency |
| Property 8 | EmbeddingPropertyTests | test_embedding_storage_retrieval |
| Property 9 | SearchPropertyTests | test_search_result_cardinality |
| Property 10 | SearchPropertyTests | test_search_result_completeness |
| Property 11 | TaskPropertyTests | test_task_creation_and_assignment |
| Property 12 | TaskPropertyTests | test_invalid_user_assignment_rejection |
| Property 13 | TaskPropertyTests | test_task_ownership_filtering |
| Property 14 | TaskPropertyTests | test_task_status_update_authorization |
| Property 15 | TaskPropertyTests | test_task_status_transition_validity |
| Property 16 | TaskPropertyTests | test_task_filtering_correctness |
| Property 17 | ActivityLogPropertyTests | test_activity_logging_completeness |
| Property 18 | AnalyticsPropertyTests | test_analytics_count_accuracy |
| Property 19 | AnalyticsPropertyTests | test_search_query_frequency_tracking |
| Property 20 | SearchPropertyTests | test_semantic_search_relevance_ordering |

### 18.6 Complementary Unit Testing

While property-based tests verify universal properties, unit tests should cover:

1. **Specific Examples**: Concrete scenarios that demonstrate correct behavior
   - Example: Login with specific known credentials
   - Example: Upload a specific test document

2. **Edge Cases**: Boundary conditions
   - Empty task descriptions
   - Maximum file size uploads
   - Zero search results

3. **Error Conditions**: Specific error scenarios
   - Malformed JWT tokens
   - SQL injection attempts
   - File upload with wrong extension

4. **Integration Points**: Component interactions
   - Database connection handling
   - File system operations
   - Vector database integration

**Balance**: Aim for 70% property tests (covering universal behaviors) and 30% unit tests (covering specific examples and edge cases).

### 18.7 Running Property Tests

```bash
# Run all property tests
pytest tests/property_tests/ -v

# Run with coverage
pytest tests/property_tests/ --cov=app --cov-report=html

# Run specific property test
pytest tests/property_tests/test_auth_properties.py::AuthenticationPropertyTests::test_jwt_token_round_trip -v

# Run with increased examples for thorough testing
pytest tests/property_tests/ --hypothesis-seed=random --hypothesis-show-statistics
```

### 18.8 Continuous Integration

Property tests MUST be included in the CI/CD pipeline:

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  property-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install hypothesis pytest-cov
      - name: Run property-based tests
        run: pytest tests/property_tests/ -v --hypothesis-show-statistics
      - name: Run unit tests
        run: pytest tests/unit_tests/ -v
```

