# Test Files Summary

Complete guide to all test files included in the project for semantic search application testing.

## Quick Reference

| File | Size | Topic | Use Case |
|------|------|-------|----------|
| test_01_authentication.txt | ~3KB | Authentication & JWT | Verify auth search functionality |
| test_02_rbac.txt | ~3KB | Role-Based Access Control | Test permission scoping |
| test_03_tasks.txt | ~3KB | Task Management | Verify task-aware search |
| test_04_vector_search.txt | ~3KB | Vector Databases & FAISS | Test semantic search |
| test_05_database.txt | ~3KB | Database Design | Test cross-domain search |
| test_06_rest_api.txt | ~3KB | RESTful API Design | Verify API endpoint searching |
| test_07_frontend_performance.txt | ~4KB | Frontend Performance | Test query variety |
| test_08_security.txt | ~5KB | Web Security | Security-related queries |

**Total Test Data:** ~25KB of document content across 8 files

---

## Test File Details

### 1. test_01_authentication.txt
**Topic:** JWT and User Authentication
**Key Concepts Covered:**
- JSON Web Tokens (JWT)
- Authentication flows
- Token structure and validation
- OAuth 2.0 and social login
- Security considerations

**Test Queries to Try:**
```
"How does JWT authentication work?"
"authenticate users in web applications"
"OAuth 2.0 implementation"
"multi factor authentication"
"token based authentication"
```

**Expected Behavior:**
- High relevance scores (0.85+) for auth-related queries
- Chunking should split by logical sections (JWT structure, security, etc.)
- Should appear in top results for user/credential-related searches

---

### 2. test_02_rbac.txt
**Topic:** Role-Based Access Control (RBAC)
**Key Concepts Covered:**
- RBAC definition and benefits
- Core RBAC components (users, roles, permissions)
- Common roles in web applications
- Implementation patterns
- Security best practices

**Test Queries to Try:**
```
"What is role based access control"
"implement RBAC in applications"
"user permissions and roles"
"principle of least privilege"
"admin moderator viewer roles"
```

**Expected Behavior:**
- Excellent matches for permission/role queries
- Properly chunked content by RBAC concept
- Should score high for access control searches

---

### 3. test_03_tasks.txt
**Topic:** Task Management and Workflow Execution
**Key Concepts Covered:**
- Task lifecycle and states
- Task prioritization and dependencies
- Task assignment and ownership
- Status tracking and progress updates
- Automation in task management

**Test Queries to Try:**
```
"task management workflow"
"task lifecycle states"
"task assignment and ownership"
"priority management"
"task dependencies"
```

**Expected Behavior:**
- Most relevant file for task-related searches
- Comprehensive chunking of task concepts
- Should rank first for task execution queries

---

### 4. test_04_vector_search.txt
**Topic:** Vector Databases and Semantic Search
**Key Concepts Covered:**
- Vector embeddings and representation
- FAISS indexing techniques
- Similarity metrics (Euclidean, Cosine, Inner Product)
- Semantic search implementation
- Scaling vector databases

**Test Queries to Try:**
```
"vector database search"
"FAISS indexing"
"semantic similarity"
"embeddings and vectors"
"similarity metrics"
```

**Expected Behavior:**
- Top result for semantic/AI-related queries
- Well-chunked technical content
- Validates system's own search mechanism comprehension

---

### 5. test_05_database.txt
**Topic:** Database Design and Normalization
**Key Concepts Covered:**
- Database normalization (1NF through BCNF)
- Foreign key relationships
- Indexing and performance
- ACID properties
- Data warehousing

**Test Queries to Try:**
```
"database normalization"
"first normal form second normal form"
"foreign key constraints"
"ACID properties"
"database indexes"
```

**Expected Behavior:**
- Captures theoretical database concepts
- Good for testing cross-cutting searches
- Demonstrates semantic grasp of data structures

---

### 6. test_06_rest_api.txt
**Topic:** RESTful API Design Best Practices
**Key Concepts Covered:**
- REST principles and constraints
- HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Status codes and error handling
- Resource naming conventions
- API versioning and documentation

**Test Queries to Try:**
```
"REST API design best practices"
"HTTP status codes"
"RESTful resource naming"
"API versioning strategies"
"CRUD operations"
```

**Expected Behavior:**
- High relevance for API design queries
- Comprehensive coverage of HTTP methods
- Good test for development-focused searches

---

### 7. test_07_frontend_performance.txt
**Topic:** Frontend Performance Optimization
**Key Concepts Covered:**
- Web Vitals (LCP, FID, CLS)
- JavaScript optimization (code splitting, tree shaking)
- CSS performance techniques
- Image optimization
- React-specific optimizations
- Performance monitoring tools

**Test Queries to Try:**
```
"frontend performance optimization"
"code splitting and tree shaking"
"lazy loading components"
"image optimization webp avif"
"web vitals LCP FID CLS"
"React performance best practices"
```

**Expected Behavior:**
- Covers modern frontend concerns
- Good for performance-related queries
- Validates system's ability to find optimization tips

---

### 8. test_08_security.txt
**Topic:** Web Application Security
**Key Concepts Covered:**
- OWASP Top 10 vulnerabilities
- SQL injection and XSS prevention
- CSRF attacks and mitigation
- Authentication and authorization
- API security (OAuth, JWT)
- Security testing approaches

**Test Queries to Try:**
```
"web application security"
"SQL injection prevention"
"cross site scripting XSS"
"CSRF attack prevention"
"OAuth 2.0 security"
"password hashing bcrypt"
"API security best practices"
```

**Expected Behavior:**
- Comprehensive security vulnerability coverage
- Excellent for security-conscious queries
- Validates system's security documentation index

---

## Testing Workflows

### Workflow 1: Basic Upload & Search
1. Upload all 8 test files via admin panel
2. Run simple searches on each topic
3. Verify all files indexed (Analytics should show 8 documents)
4. Record search latencies

**Expected Time:** 5-10 minutes
**Success Criteria:** All files appear in search results

---

### Workflow 2: Semantic Quality Validation
1. Upload test files
2. Run the test queries from each file's section above
3. Check relevance scores for each
4. Compare semantic vs keyword matching

**Expected Time:** 10-15 minutes
**Success Criteria:** Avg score > 0.82 for top results

---

### Workflow 3: Task-Aware Search
1. Create task: "Learn API Design and Security"
2. Assign to task: test_06_rest_api.txt + test_08_security.txt
3. Search for "API security" while filtering by task
4. Verify only assigned documents appear

**Expected Time:** 5 minutes
**Success Criteria:** Task filter limits results to 2 documents

---

### Workflow 4: Performance Baseline
1. Record: Search latency with 8 documents
2. Measure: Index rebuild time
3. Monitor: Memory usage during indexing
4. Compare: Single query latency vs analytics query

**Expected Metrics:**
- Search latency: 50-150ms
- Index rebuild: <5 minutes
- Memory: <500MB for 8 documents
- Analytics query: <100ms

---

### Workflow 5: Error Handling
1. Upload malformed document (binary file)
2. Search with empty query
3. Search with very long query (>1000 chars)
4. Stop backend and test frontend feedback
5. Try accessing admin pages as regular user

**Success Criteria:** Graceful errors, no crashes

---

## Test Data Statistics

```
Total Documents: 8
Total Content: ~25 KB
Average Doc Size: 3.1 KB
Total Chunks (estimated): 150-200
  - Each chunk: 500 words average
  - Each doc: 20-25 chunks

Topics Covered:
- Backend/Infrastructure: 3 (Auth, RBAC, Database)
- Frontend: 2 (Performance, general web practices)
- DevOps/API: 2 (REST API, Security)
- AI/ML: 1 (Vector Search)
- Distributed: 1 (Tasks)

Vocabulary Coverage:
- Technical depth: Advanced (university-level concepts)
- Business relevance: High (production system concerns)
- Cross-cutting: Yes (covers full system)
```

---

## Upload Instructions

### Via Admin Panel (GUI)
1. Navigate to http://localhost:5173
2. Login as admin (admin/password)
3. Go to "Upload Document"
4. Select file from `backend/data/`
5. Add title and description
6. Click "Upload"

### Via CLI (For Bulk Upload)
```bash
cd backend
python manage.py shell

from app.models import Document, User
from django.core.files.base import ContentFile

admin = User.objects.get(username='admin')
for filename in ['test_01_authentication.txt', 'test_02_rbac.txt', ...]:
    with open(f'data/{filename}', 'r') as f:
        content = f.read()
    doc = Document.objects.create(
        title=filename.replace('.txt', '').replace('test_', '').replace('_', ' '),
        uploaded_by=admin
    )
    # Additional setup...
```

---

## Verification Checklist

After uploading all test files:

- [ ] Admin dashboard shows 8 documents
- [ ] Total chunks indexed: 150-200
- [ ] Search returns results for all 8 topics
- [ ] Analytics dashboard responsive
- [ ] No errors in browser console
- [ ] Search latency <200ms
- [ ] Relevance scores in 0.70-0.95 range
- [ ] Task assignment works with test files
- [ ] Index rebuild completes <5 sec
- [ ] Memory usage stable

---

## Performance Expectations

With 8 test documents:

| Metric | Expected | Actual |
|--------|----------|--------|
| Total indexing time | <30 seconds | _____ |
| Search latency | 50-150ms | _____ |
| Average relevance | 0.82+ | _____ |
| Index file size | ~2-5 MB | _____ |
| Memory at idle | <200MB | _____ |
| Memory during search | <300MB | _____ |

---

## Troubleshooting

**Issue:** Documents not searchable after upload
- Solution: Check index rebuild in admin dashboard
- Verify backend logs for errors

**Issue:** Very low relevance scores (<0.60)
- Solution: Verify documents are chunked correctly
- Check FAISS index size in admin stats
- Rebuild index from scratch

**Issue:** Search timeout
- Solution: Reduce max results in search config
- Check backend resource usage
- Verify database connection stable

**Issue:** File upload fails
- Solution: Check file size vs MAX_UPLOAD_SIZE_MB
- Verify file is plain text (.txt)
- Check disk space available

---

## Next Steps After Testing

1. **Document Testing Results:**
   - Record latencies and scores
   - Note any errors or anomalies
   - Take screenshots for presentation

2. **Create Custom Test Files:**
   - Add domain-specific documents
   - Test with larger files (>10MB)
   - Test with multiple languages

3. **Performance Optimization:**
   - Profile search queries
   - Identify bottlenecks
   - Implement caching if needed

4. **Deploy to Production:**
   - Use these test files on production
   - Monitor real-world performance
   - Collect user search metrics

---

## Test Files Location

All test files are located in: `backend/data/`

```
backend/data/
├── test_01_authentication.txt
├── test_02_rbac.txt
├── test_03_tasks.txt
├── test_04_vector_search.txt
├── test_05_database.txt
├── test_06_rest_api.txt
├── test_07_frontend_performance.txt
└── test_08_security.txt
```

---

**Created:** 2026-04-10  
**Test Files Version:** 1.0  
**Status:** Ready for use
