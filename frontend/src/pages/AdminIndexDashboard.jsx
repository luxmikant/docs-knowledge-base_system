import { useState, useEffect } from 'react';
import * as searchAPI from '../api/search';
import '../styles/admin.css';

export default function AdminIndexDashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const [rebuildingIndex, setRebuildingIndex] = useState(false);
  const [optimizingIndex, setOptimizingIndex] = useState(false);
  
  const loadStats = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await searchAPI.getIndexStats();
      setStats(response.data);
    } catch (err) {
      setError('Failed to load index statistics');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    loadStats();
    // Refresh stats every 30 seconds
    const interval = setInterval(loadStats, 30000);
    return () => clearInterval(interval);
  }, []);
  
  const handleRebuildIndex = async () => {
    if (!window.confirm('Rebuild the entire search index? This may take a few minutes.')) {
      return;
    }
    
    setRebuildingIndex(true);
    setError('');
    setSuccess('');
    
    try {
      const response = await searchAPI.rebuildSearchIndex();
      setSuccess('✓ Index rebuilt successfully');
      setStats(response.data.stats);
    } catch (err) {
      setError('Failed to rebuild index');
      console.error(err);
    } finally {
      setRebuildingIndex(false);
    }
  };
  
  const handleOptimizeIndex = async () => {
    setOptimizingIndex(true);
    setError('');
    setSuccess('');
    
    try {
      await searchAPI.optimizeIndex();
      setSuccess('✓ Index optimized successfully');
      await loadStats();
    } catch (err) {
      setError('Failed to optimize index');
      console.error(err);
    } finally {
      setOptimizingIndex(false);
    }
  };
  
  if (!stats && loading) {
    return <div className="admin-dashboard"><p>Loading index statistics...</p></div>;
  }
  
  return (
    <section className="admin-dashboard">
      <h2>🛠️ Search Index Administration</h2>
      
      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}
      
      {/* Index Statistics */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Documents</div>
          <div className="stat-value">{stats?.total_documents || 0}</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-label">Total Chunks</div>
          <div className="stat-value">{stats?.total_chunks || 0}</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-label">Indexed Vectors</div>
          <div className="stat-value">{stats?.indexed_vectors || 0}</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-label">Index Ratio</div>
          <div className="stat-value">
            {stats && stats.total_chunks > 0
              ? ((stats.indexed_vectors / stats.total_chunks) * 100).toFixed(1)
              : 0}
            %
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-label">Map Entries</div>
          <div className="stat-value">{stats?.chunk_map_entries || 0}</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-label">Cache Hit Rate</div>
          <div className="stat-value">{stats?.cache_hit_rate || 0}%</div>
        </div>
      </div>
      
      {/* Actions */}
      <div className="actions-panel">
        <h3>Maintenance Actions</h3>
        
        <div className="action-group">
          <button
            className="btn btn-primary"
            onClick={handleOptimizeIndex}
            disabled={optimizingIndex}
          >
            {optimizingIndex ? '🔄 Optimizing...' : '⚡ Optimize Index'}
          </button>
          <small className="action-hint">
            Remove orphaned entries and clean up index structure
          </small>
        </div>
        
        <div className="action-group">
          <button
            className="btn btn-danger"
            onClick={handleRebuildIndex}
            disabled={rebuildingIndex}
          >
            {rebuildingIndex ? '🔄 Rebuilding...' : '🔨 Rebuild Index'}
          </button>
          <small className="action-hint">
            Completely rebuild index from all documents (takes longer)
          </small>
        </div>
        
        <div className="action-group">
          <button
            className="btn btn-secondary"
            onClick={loadStats}
            disabled={loading}
          >
            {loading ? '🔄 Refreshing...' : '🔄 Refresh Stats'}
          </button>
          <small className="action-hint">
            Reload current index statistics
          </small>
        </div>
      </div>
      
      {/* Health Check */}
      <div className="health-check">
        <h3>Index Health</h3>
        
        {stats && (
          <div className="health-items">
            <div className="health-item">
              <span className="health-label">Documents Indexed:</span>
              <span className={stats.total_documents > 0 ? 'status-ok' : 'status-warning'}>
                {stats.total_documents > 0 ? '✓' : '⚠'} {stats.total_documents} documents
              </span>
            </div>
            
            <div className="health-item">
              <span className="health-label">Vector Count:</span>
              <span className={stats.indexed_vectors === stats.total_chunks ? 'status-ok' : 'status-warning'}>
                {stats.indexed_vectors === stats.total_chunks ? '✓' : '⚠'} 
                {stats.indexed_vectors} vectors ({((stats.indexed_vectors / (stats.total_chunks || 1)) * 100).toFixed(1)}%)
              </span>
            </div>
            
            <div className="health-item">
              <span className="health-label">Consistency:</span>
              <span className={stats.chunk_map_entries === stats.indexed_vectors ? 'status-ok' : 'status-warning'}>
                {stats.chunk_map_entries === stats.indexed_vectors ? '✓' : '⚠'} 
                Map entries match indexed vectors
              </span>
            </div>
          </div>
        )}
      </div>
      
      {/* Info Box */}
      <div className="info-box">
        <h4>💡 Index Optimization Tips</h4>
        <ul>
          <li><strong>Optimize daily:</strong> Removes orphaned entries and improves performance</li>
          <li><strong>Monitor vector count:</strong> Should match total chunks in database</li>
          <li><strong>Cache hit rate:</strong> Higher is better for repeated queries</li>
          <li><strong>Rebuild when:</strong> After bulk document deletions or major schema changes</li>
        </ul>
      </div>
    </section>
  );
}
