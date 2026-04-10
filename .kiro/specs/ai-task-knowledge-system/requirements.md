# Requirements: AI-Powered Task & Knowledge Management System

## 1. Overview

Build an MVP system where admins can upload documents and assign tasks, while users can search documents using AI-powered semantic search and complete assigned tasks.

## 2. User Roles

### 2.1 Admin Role
- Can upload and manage documents
- Can create and assign tasks to users
- Can view analytics and activity logs
- Has full system access

### 2.2 User Role
- Can search documents using AI-powered semantic search
- Can view assigned tasks
- Can update task status (Pending → Completed)
- Can access knowledge base

## 3. Functional Requirements

### 3.1 Authentication & Authorization

**3.1.1 User Authentication**
- System must implement JWT-based authentication
- Users must be able to login with credentials
- JWT tokens must be used for API authorization
- Activity logging must track all login attempts

**Acceptance Criteria:**
- User can login with valid credentials and receive JWT token
- Invalid credentials return appropriate error message
- JWT token is required for protected endpoints
- Token expiration is handled properly

**3.1.2 Role-Based Access Control (RBAC)**
- System must enforce role-based permissions
- Admin-only endpoints must reject User role requests
- Each API endpoint must validate user role

**Acceptance Criteria:**
- Admin can access all endpoints
- User can only access user-permitted endpoints
- Unauthorized access returns 403 Forbidden
- Role validation occurs on every protected request

### 3.2 Document Management

**3.2.1 Document Upload**
- Admin must be able to upload .txt files (PDF optional)
- System must store document metadata (filename, upload date, uploader)
- Documents must be processed for AI search capabilities
- Activity logging must track document uploads

**Acceptance Criteria:**
- Admin can successfully upload .txt files
- Document metadata is stored in database
- Document content is extracted and prepared for embedding
- Upload activity is logged with timestamp and admin ID

**3.2.2 Document Storage**
- Documents must be stored with proper metadata
- System must maintain document-user relationships
- Documents must be retrievable by ID

**Acceptance Criteria:**
- Each document has unique ID
- Metadata includes: filename, upload_date, uploaded_by, file_size
- Documents can be retrieved via API

### 3.3 AI-Powered Semantic Search

**3.3.1 Embedding Generation**
- System must convert document text into embeddings
- Embeddings must be generated using appropriate model
- Embeddings must be stored in vector database (FAISS or Chroma)

**Acceptance Criteria:**
- Document text is successfully converted to embeddings
- Embeddings are stored in vector database
- Vector database is queryable
- Embedding generation does not rely solely on external LLM APIs

**3.3.2 Semantic Search**
- Users must be able to search documents using natural language queries
- System must convert query to embedding
- System must retrieve relevant documents based on semantic similarity
- Search results must be ranked by relevance
- Activity logging must track search queries

**Acceptance Criteria:**
- User can submit natural language search query
- Query is converted to embedding
- Top-k relevant documents are returned
- Results include document content and relevance score
- Search activity is logged with query text and user ID

### 3.4 Task Management

**3.4.1 Task Creation (Admin)**
- Admin must be able to create tasks
- Tasks must include: title, description, assigned_to (user_id), status
- Tasks must be assigned to specific users
- Activity logging must track task creation

**Acceptance Criteria:**
- Admin can create task with required fields
- Task is stored in database with proper relationships
- Assigned user can view the task
- Task creation is logged

**3.4.2 Task Assignment**
- Admin must be able to assign tasks to users
- System must validate that assigned user exists
- Users must be able to view only their assigned tasks

**Acceptance Criteria:**
- Admin can assign task to valid user
- Invalid user ID returns error
- User can retrieve their assigned tasks via API
- Assignment is tracked in database

**3.4.3 Task Status Management**
- Users must be able to update task status
- Valid status transitions: Pending → Completed
- Activity logging must track status changes

**Acceptance Criteria:**
- User can update status of their assigned tasks
- Status change is persisted in database
- User cannot update tasks assigned to others
- Status update is logged with timestamp

**3.4.4 Task Filtering**
- API must support dynamic filtering of tasks
- Filters must include: status, assigned_to
- Multiple filters can be combined

**Acceptance Criteria:**
- GET /tasks?status=completed returns only completed tasks
- GET /tasks?assigned_to=17 returns tasks for user 17
- Filters can be combined: /tasks?status=pending&assigned_to=17
- Invalid filter values return appropriate error

### 3.5 Activity Logging

**3.5.1 Activity Tracking**
- System must log key user actions
- Logged actions must include: login, task update, document upload, search
- Logs must include: user_id, action_type, timestamp, details

**Acceptance Criteria:**
- Login attempts are logged
- Task status updates are logged
- Document uploads are logged
- Search queries are logged
- Logs are stored in activity_logs table

### 3.6 Analytics

**3.6.1 Task Analytics**
- System must provide total task count
- System must show completed vs pending task breakdown
- Analytics must be accessible via API

**Acceptance Criteria:**
- GET /analytics returns total tasks
- Response includes completed count and pending count
- Counts are accurate and real-time

**3.6.2 Search Analytics**
- System must track most searched queries
- System must provide search query count

**Acceptance Criteria:**
- Analytics include most frequent search queries
- Search count is accurate
- Data is retrievable via API

## 4. Non-Functional Requirements

### 4.1 Technology Stack

**4.1.1 Backend**
- Must use Python (FastAPI or Django)
- Must use MySQL database
- Must implement proper relational schema with PK/FK
- Must use JWT for authentication

**4.1.2 Frontend**
- Must use React.js
- Must implement proper state management
- Must integrate with backend APIs

**4.1.3 AI Components**
- Must use embedding model for text vectorization
- Must use vector database (FAISS or Chroma)
- Must NOT rely solely on external LLM APIs
- Core search logic must be implemented locally

### 4.2 Database Schema

**4.2.1 Required Tables**
- users (id, username, email, password_hash, role_id, created_at)
- roles (id, role_name)
- tasks (id, title, description, assigned_to, created_by, status, created_at, updated_at)
- documents (id, filename, file_path, uploaded_by, upload_date, file_size)
- activity_logs (id, user_id, action_type, details, timestamp)

**4.2.2 Relationships**
- users.role_id → roles.id (FK)
- tasks.assigned_to → users.id (FK)
- tasks.created_by → users.id (FK)
- documents.uploaded_by → users.id (FK)
- activity_logs.user_id → users.id (FK)

### 4.3 API Endpoints

**Required Endpoints:**
- POST /auth/login
- GET /tasks (with filtering support)
- POST /tasks (admin only)
- PUT /tasks/{id} (status update)
- POST /documents (admin only)
- GET /documents
- POST /search
- GET /analytics

### 4.4 Code Quality

**4.4.1 Architecture**
- Clean separation of concerns (models, services, controllers)
- Proper folder structure
- Maintainable and scalable code
- Clear naming conventions

**4.4.2 Documentation**
- README with setup instructions
- Tech stack documentation
- API documentation
- Architecture explanation

## 5. Success Criteria

The system is considered successful when:
- All authentication and RBAC requirements are met
- Document upload and AI search work correctly
- Task management flows work end-to-end
- Activity logging captures all required actions
- Analytics provide accurate insights
- Code is clean, well-structured, and maintainable
- System can be set up and run following README instructions

## 6. Out of Scope

- User registration (assume users are pre-created)
- Password reset functionality
- Email notifications
- Advanced document formats beyond .txt (PDF is optional)
- Real-time updates/websockets
- Mobile application
- Advanced analytics dashboards
