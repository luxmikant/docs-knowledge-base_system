import { useState } from 'react';
import api from '../api/client';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const runSearch = async (event) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await api.post('/search', { query, top_k: 5 });
      setResults(response.data.results || []);
    } catch (err) {
      setError(err?.response?.data?.error || 'Search failed');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section>
      <h2>Semantic Search</h2>
      <form className="panel" onSubmit={runSearch}>
        <input
          placeholder="Ask in natural language..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          required
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {error && <div className="error-box">{error}</div>}

      <div className="panel">
        <h3>Results</h3>
        {results.length === 0 ? (
          <p>No results yet.</p>
        ) : (
          <div className="list">
            {results.map((result) => (
              <article key={result.document_id} className="list-item stacked">
                <div>
                  <h4>{result.filename}</h4>
                  <small>Score: {result.relevance_score}</small>
                </div>
                <p>{result.content_snippet}</p>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
