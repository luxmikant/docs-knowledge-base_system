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
      <h2>Analytics</h2>

      <div className="metric-grid">
        <article className="metric-card">
          <h4>Total Tasks</h4>
          <p>{analytics.tasks.total}</p>
        </article>
        <article className="metric-card">
          <h4>Completed Tasks</h4>
          <p>{analytics.tasks.completed}</p>
        </article>
        <article className="metric-card">
          <h4>Pending Tasks</h4>
          <p>{analytics.tasks.pending}</p>
        </article>
        <article className="metric-card">
          <h4>Total Documents</h4>
          <p>{analytics.documents.total}</p>
        </article>
        <article className="metric-card">
          <h4>Total Searches</h4>
          <p>{analytics.searches.total_queries}</p>
        </article>
        <article className="metric-card">
          <h4>Document Size (MB)</h4>
          <p>{analytics.documents.total_size_mb}</p>
        </article>
      </div>

      <div className="panel">
        <h3>Top Queries</h3>
        {analytics.searches.top_queries.length === 0 ? (
          <p>No search query data yet.</p>
        ) : (
          <ul>
            {analytics.searches.top_queries.map((query) => (
              <li key={query.query}>
                {query.query} ({query.count})
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
