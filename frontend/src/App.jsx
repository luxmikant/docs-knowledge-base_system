import { Navigate, Route, Routes } from 'react-router-dom';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import AuthPage from './pages/AuthPage';
import TasksPage from './pages/TasksPage';
import DocumentsPage from './pages/DocumentsPage';
import SearchPage from './pages/SearchPage';
import EnhancedSearchPage from './pages/EnhancedSearchPage';
import AnalyticsPage from './pages/AnalyticsPage';
import AdminIndexDashboard from './pages/AdminIndexDashboard';

function AppRoutes() {
  return (
    <Routes>
      <Route path="/auth" element={<AuthPage />} />
      <Route
        path="/tasks"
        element={
          <ProtectedRoute>
            <Layout>
              <TasksPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/documents"
        element={
          <ProtectedRoute>
            <Layout>
              <DocumentsPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/search"
        element={
          <ProtectedRoute>
            <Layout>
              <SearchPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/search/advanced"
        element={
          <ProtectedRoute>
            <Layout>
              <EnhancedSearchPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/index"
        element={
          <ProtectedRoute adminOnly>
            <Layout>
              <AdminIndexDashboard />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/analytics"
        element={
          <ProtectedRoute adminOnly>
            <Layout>
              <AnalyticsPage />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/tasks" replace />} />
    </Routes>
  );
}

export default function App() {
  return <AppRoutes />;
}
