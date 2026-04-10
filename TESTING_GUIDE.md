TESTING GUIDE: AI-Powered Knowledge Base with Semantic Search

Overview
This document provides comprehensive testing instructions for the AI-powered knowledge base application. The system includes semantic search, task management, role-based access control, and analytics.

Setup for Testing

1. Start the Backend Server
cd backend
python manage.py migrate
python manage.py runserver
# Backend runs on http://localhost:8000

2. Start the Frontend
cd frontend
npm install
npm run dev
# Frontend runs on http://localhost:5173

3. Default Test Credentials
- Admin User: username=admin, password=password
- Regular User: username=user1, password=password

Test Files Provided
Located in: backend/data/
- test_01_authentication.txt - JWT and auth concepts
- test_02_rbac.txt - Role-based access control
- test_03_tasks.txt - Task management workflows
- test_04_vector_search.txt - Vector databases and semantic search

Upload these documents via the admin dashboard to test the search functionality.

Core Features to Test

1. Authentication & Authorization
---
Flow:
1. Go to http://localhost:5173
2. Login with admin credentials (admin/password)
3. Verify JWT token is stored in localStorage
4. Test accessing protected routes
5. Logout and verify redirect to login

Expected Results:
- Successful login redirects to /
- LocalStorage contains 'token' key with JWT
- Unauthorized access returns 401 error
- Logout clears token and redirects to /login

2. Document Upload (Admin Only)
---
Flow:
1. Login as admin
2. Navigate to "Document Upload" 
3. Select one of the test files from backend/data/
4. Fill in document description
5. Click upload

Expected Results:
- Document appears in the documents list
- File is stored in media/documents/
- Status shows "Uploaded"
- Can see in admin dashboard

Test with all 4 provided test files:
- test_01_authentication.txt
- test_02_rbac.txt
- test_03_tasks.txt
- test_04_vector_search.txt

3. Semantic Search (Basic)
---
Flow:
1. Login as any user
2. Go to Search page
3. Enter search query
4. View results

Test Queries and Expected Results:
Query: "authenticate users"
Expected: test_01_authentication.txt should rank high (0.85+)
Chunks about JWT, passwords, OAuth should appear

Query: "role based access"
Expected: test_02_rbac.txt should rank high (0.88+)
Chunks about RBAC implementation should appear

Query: "task management workflow"
Expected: test_03_tasks.txt should rank high (0.87+)
Task lifecycle, assignment chunks should appear

Query: "vector database search"
Expected: test_04_vector_search.txt should rank high (0.85+)
FAISS, embeddings, similarity search chunks should appear

Relevance Scores:
- 0.90+ : Excellent match
- 0.80-0.89 : Good match
- 0.70-0.79 : Acceptable match
- <0.70 : Weak match

4. Hybrid Search
---
Flow:
1. Go to Enhanced Search page (/search/advanced)
2. Enter query: "JWT tokens security"
3. Toggle to Hybrid mode (if available)
4. Adjust semantic weight (default 70%, keyword 30%)
5. View results

Expected Results:
- Results include both semantic + keyword matches
- Documents containing "JWT", "tokens", "security" appear
- Relevance scores displayed for both methods
- Top chunks highlighted

5. Task-Aware Search
---
Flow:
1. Login as admin
2. Create a task (e.g., "Implement authentication")
3. Assign documents to the task:
   - Add test_01_authentication.txt
4. Login as assigned user
5. Search for "how to authenticate"
6. Filter by task "Implement authentication"

Expected Results:
- Only documents assigned to task appear
- Search results scoped to task documents
- Relevance scores adjusted for task context

6. Role-Based Access Control
---
Test Admin Access:
1. Login as admin
2. Navigate to:
   - Document Upload (/admin/upload) - should be accessible
   - Index Dashboard (/admin/index) - should be accessible
   - Analytics (/analytics) - should be accessible
3. Expected: All pages accessible

Test User Access:
1. Login as user1
2. Try accessing admin pages
3. Expected: Redirect to home or show "Unauthorized"

7. Index Management Dashboard
---
Flow:
1. Login as admin
2. Go to Admin > Index Dashboard
3. View metrics:
   - Total indexed chunks
   - Cache hit rate
   - Index consistency status

4. Perform operations:
   - Click "Optimize Index" - removes orphaned entries
   - Click "Rebuild Index" - full reindex

Expected Results:
- Metrics update in real-time
- Operations complete without errors
- Index consistency maintained

8. Analytics Dashboard
---
Flow:
1. Login as admin
2. Navigate to Analytics (/analytics)
3. View metrics:
   - Total tasks (should show count)
   - Completed tasks (should show progress)
   - Total searches (should increase as you search)
   - Active users (should update)
   - Documents uploaded (should match uploads)

4. View breakdowns:
   - Top queries in last 7 days
   - Searches by user
   - Document uploads by user
   - System health status

Expected Results:
- All metrics display without errors
- No undefined values or null errors
- System health shows green/healthy
- Data reflects actual activity

9. Activity Logging
---
Flow:
1. Perform actions:
   - Login
   - Upload document
   - Search for documents
   - Complete a task
2. Check activity logs (if available in admin)

Expected Results:
- Each action logged with timestamp
- Activity log shows user, action type, details
- Timestamps in correct timezone
- Searchable activity history

10. Performance Testing
---
Measure:
1. Search latency: Time from query to results
   Expected: <200ms for <1000 documents
   
2. Upload latency: Time from upload to indexing
   Expected: <5 seconds for documents <1MB
   
3. Index rebuild time: Time to rebuild full index
   Expected: <30 seconds for <10,000 chunks

4. Frontend load time:
   Expected: Initial page load <3 seconds
   Subsequent routes <1 second

Error Handling Tests

1. Invalid Upload
---
- Try uploading non-text file (image, binary)
- Expected: Error message "Invalid file type"

2. Invalid Search Query
---
- Empty search: ""
- Expected: Show "Enter a search query"
  
- Very long query (>1000 chars)
- Expected: Truncate or show error

3. Access Control Violations
---
- Access /admin routes as regular user
- Expected: Redirect to home or 403 forbidden

4. Network Error Simulation
---
- Stop backend server
- Try searching
- Expected: Graceful error message "Backend unavailable"

5. Index Consistency
---
- Upload document
- Manually delete from database
- Check index stats
- Expected: Index shows discrepancy, cleanup removes orphan

Test Data Scenarios

Scenario 1: Full Workflow (Admin)
1. Login as admin
2. Upload all 4 test documents
3. Create a task "Learn System Architecture"
4. Assign test_04_vector_search.txt to task
5. Verify document appears in task details
6. View analytics - should show:
   - 4 documents uploaded
   - 1 task created
   - Chunks indexed for each document

Scenario 2: Search Workflow (User)
1. Login as user1
2. Search "how does authentication work"
3. Should find test_01_authentication.txt
4. Search "organizational roles"
5. Should find test_02_rbac.txt
6. Search "task status tracking"
7. Should find test_03_tasks.txt
8. Check analytics - searches should increment

Scenario 3: Task Execution (User + Admin)
1. Admin creates task "Understand Vector Search"
2. Admin assigns test_04_vector_search.txt
3. Admin assigns to user1
4. User1 views task, searches "FAISS indexing"
5. Results scoped to assigned document
6. User1 marks task complete
7. Admin views analytics - task shows as completed

Scenario 4: Analytics Tracking
1. Multiple users perform searches
2. Wait a few minutes
3. Admin checks analytics:
   - Should see multiple searches recorded
   - Average results per search calculated
   - User distribution visible
4. Export/download stats (if available)

Database Verification

Check SQLite/MySQL for correct data:

Document Records:
SELECT * FROM app_document LIMIT 5;
Expected: 4 test documents visible

Chunk Records:
SELECT COUNT(*) FROM app_chunk;
Expected: >100 chunks (depends on document size)

Task Records:
SELECT * FROM app_task;
Expected: Created tasks visible

Activity Logs:
SELECT * FROM activity_logs ORDER BY timestamp DESC LIMIT 10;
Expected: Recent user activities logged

Troubleshooting During Tests

Issue: Backend connection refused
Solution: Ensure backend running on http://localhost:8000
Check: python manage.py runserver output

Issue: Frontend not loading
Solution: Clear browser cache, hard refresh (Ctrl+Shift+R)
Check: npm run dev output for build errors

Issue: Search returns no results
Solution: 
1. Verify documents uploaded (check admin dashboard)
2. Verify index rebuilt (Admin > Index Dashboard > Rebuild)
3. Check search query matches document content

Issue: Timeout on search
Solution:
1. Reduce number of documents or chunks
2. Clear old data from database
3. Rebuild index

Issue: Analytics shows undefined values
Solution:
1. Ensure backend /api/analytics endpoint working
2. Check browser console for errors
3. Verify data in database exists

Success Criteria

✅ All authentication flows work (login/logout/JWT)
✅ Documents upload and index successfully
✅ Search returns relevant results (0.80+ scores)
✅ Semantic vs keyword search distinguishable
✅ Task-aware filtering works correctly
✅ RBAC enforced (admin vs user pages)
✅ Analytics dashboard shows accurate metrics
✅ Index optimization completes without errors
✅ No JavaScript errors in browser console
✅ All API endpoints respond (<500ms)
✅ Activity logs capture all actions
✅ No database integrity issues

Regression Test Checklist

After Each Code Change:
☐ Login still works (auth flow)
☐ Search returns results (core feature)
☐ No new JavaScript errors
☐ Index health status good
☐ Analytics dashboard loads
☐ Admin pages accessible only to admins
☐ No database errors in logs

Performance Regression:
☐ Search latency not increased >50%
☐ Upload speed maintained
☐ Frontend load time <3s
☐ Memory usage stable

Next Steps

1. Execute all test scenarios in order
2. Document any failures with:
   - Browser console errors
   - Backend server errors
   - Expected vs actual results
3. Create bug reports for issues found
4. Re-test after fixes applied
5. Collect performance metrics for baseline

---
Last Updated: 2026-04-10
Test Files Version: 1.0
System: AI-Powered Knowledge Base with Semantic Search
