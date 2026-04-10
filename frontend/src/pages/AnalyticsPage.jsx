import { useEffect, useState } from 'react';
import api from '../api/client';

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const response = await api.get('/analytics');
        setAnalytics(response.data);
      } catch (err) {
        setError(err?.response?.data?.error || 'Failed to load analytics');
      }
    };

    load();
  }, []);

  if (error) {
    return <div className="error-box">{error}</div>;
  }

  if (!analytics) {
    return <p>Loading analytics...</p>;
  }

  return (
    <section>
      <h2>📊 Analytics Dashboard</h2>

      <div className="metric-grid">
        <article className="metric-card">
          <h4>Total Tasks</h4>
          <p className="metric-value">{analytics.tasks?.total_tasks ?? 0}</p>
          <small>All tasks</small>
        </article>
        <article className="metric-card">
          <h4>Completed Tasks</h4>
          <p className="metric-value">{analytics.tasks?.completed_tasks ?? 0}</p>
          <small>Finished</small>
        </article>
        <article className="metric-card">
          <h4>Pending Tasks</h4>
          <p className="metric-value">{analytics.tasks?.pending_tasks ?? 0}</p>
          <small>In progress</small>
        </article>
        <article className="metric-card">
          <h4>Completion Rate</h4>
          <p className="metric-value">{analytics.tasks?.completion_rate ?? 0}%</p>
          <small>Task completion</small>
        </article>
        <article className="metric-card">
          <h4>Total Documents</h4>
          <p className="metric-value">{analytics.documents?.total_documents ?? 0}</p>
          <small>Uploaded</small>
        </article>
        <article className="metric-card">
          <h4>Total Searches</h4>
          <p className="metric-value">{analytics.search?.total_searches ?? 0}</p>
          <small>Last 7 days</small>
        </article>
        <article className="metric-card">
          <h4>Active Users</h4>
          <p className="metric-value">{analytics.users?.active_users ?? 0}</p>
          <small>This week</small>
        </article>
        <article className="metric-card">
          <h4>Total Chunks</h4>
          <p className="metric-value">{analytics.documents?.total_chunks ?? 0}</p>
          <small>Indexed for search</small>
        </article>
      </div>

      <div className="analytics-grid">
        <div className="panel">
          <h3>📈 Top Queries (Last 7 Days)</h3>
          {!analytics.search?.top_queries || analytics.search.top_queries.length === 0 ? (
            <p>No search queries yet.</p>
          ) : (
            <ul>
              {analytics.search.top_queries.slice(0, 5).map((query, idx) => (
                <li key={idx}>
                  <span>{query.details || 'N/A'}</span>
                  <span className="count">{query.count}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="panel">
          <h3>👥 Searches by User</h3>
          {!analytics.search?.searches_by_user || analytics.search.searches_by_user.length === 0 ? (
            <p>No search activity.</p>
          ) : (
            <ul>
              {analytics.search.searches_by_user.slice(0, 5).map((user, idx) => (
                <li key={idx}>
                  <span>{user.user__username || user}</span>
                  <span className="count">{user.count}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="panel">
          <h3>📤 Documents by User</h3>
          {!analytics.documents?.uploads_by_user || analytics.documents.uploads_by_user.length === 0 ? (
            <p>No documents uploaded.</p>
          ) : (
            <ul>
              {analytics.documents.uploads_by_user.slice(0, 5).map((user, idx) => (
                <li key={idx}>
                  <span>{user.uploaded_by__username || user}</span>
                  <span className="count">{user.count} docs</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="panel">
          <h3>🔧 System Health</h3>
          {analytics.system_health && (
            <>
              <ul>
                <li>
                  <span>Indexed Chunks</span>
                  <span className="count">{analytics.system_health.indexed_chunks ?? 0}</span>
                </li>
                <li>
                  <span>Database Chunks</span>
                  <span className="count">{analytics.system_health.database_chunks ?? 0}</span>
                </li>
                <li>
                  <span>Index Status</span>
                  <span className={`status ${analytics.system_health.index_consistent ? 'healthy' : 'warning'}`}>
                    {analytics.system_health.index_consistent ? '✓ Healthy' : '⚠ Issues'}
                  </span>
                </li>
              </ul>
            </>
          )}
        </div>
      </div>
    </section>
  );
}
