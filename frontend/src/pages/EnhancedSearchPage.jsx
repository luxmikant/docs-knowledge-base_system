import { useState, useEffect } from 'react';
import * as searchAPI from '../api/search';
import '../styles/search.css';

export default function EnhancedSearchPage() {
  // Search inputs
  const [query, setQuery] = useState('');
  const [searchMode, setSearchMode] = useState('semantic'); // 'semantic' or 'hybrid'
  const [selectedTaskId, setSelectedTaskId] = useState('');
  const [topK, setTopK] = useState(10);
  const [minScore, setMinScore] = useState(0.3);
  
  // Hybrid search weights
  const [semanticWeight, setSemanticWeight] = useState(0.7);
  const [keywordWeight, setKeywordWeight] = useState(0.3);
  
  // Results
  const [results, setResults] = useState([]);
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Tasks
  const [tasks, setTasks] = useState([]);
  const [taskDocuments, setTaskDocuments] = useState(null);
  
  // Filters
  const [expandedFilters, setExpandedFilters] = useState(false);
  const [sortBy, setSortBy] = useState('relevance'); // 'relevance', 'recency', 'popularity'
  
  // Load tasks on mount
  useEffect(() => {
    const loadTasks = async () => {
      try {
        const response = await searchAPI.api.get('/tasks');
        setTasks(response.data.tasks || []);
      } catch (err) {
        console.error('Failed to load tasks:', err);
      }
    };
    loadTasks();
  }, []);
  
  // Load task documents when task is selected
  useEffect(() => {
    if (selectedTaskId) {
      const loadTaskDocs = async () => {
        try {
          const response = await searchAPI.getTaskDocuments(selectedTaskId);
          setTaskDocuments(response.data.documents || []);
        } catch (err) {
          console.error('Failed to load task documents:', err);
        }
      };
      loadTaskDocs();
    } else {
      setTaskDocuments(null);
    }
  }, [selectedTaskId]);
  
  const runSearch = async (event) => {
    event.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      let response;
      
      if (searchMode === 'hybrid') {
        response = await searchAPI.hybridSearch(
          query,
          topK,
          minScore,
          semanticWeight,
          keywordWeight
        );
      } else if (selectedTaskId) {
        response = await searchAPI.taskAwareSearch(query, selectedTaskId, topK, minScore);
      } else {
        response = await searchAPI.search(query, topK, minScore);
      }
      
      setResults(response.data.results || []);
      setMetadata(response.data.metadata || null);
    } catch (err) {
      setError(err?.response?.data?.error || 'Search failed');
      setResults([]);
      setMetadata(null);
    } finally {
      setLoading(false);
    }
  };
  
  const getScoreColor = (score) => {
    if (score >= 0.8) return '#2d7a2d'; // Green
    if (score >= 0.6) return '#7a7a2d'; // Yellow-ish
    if (score >= 0.4) return '#7a4a2d'; // Orange-ish
    return '#7a2d2d'; // Red
  };
  
  return (
    <section className="search-container">
      <h2>Advanced Search</h2>
      
      <form className="search-form panel" onSubmit={runSearch}>
        <div className="search-header">
          <input
            type="text"
            placeholder="Ask in natural language..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="search-input"
            required
          />
          <button type="submit" disabled={loading} className="btn-search">
            {loading ? '🔍 Searching...' : '🔍 Search'}
          </button>
        </div>
        
        {/* Mode Selection */}
        <div className="search-modes">
          <label>
            <input
              type="radio"
              value="semantic"
              checked={searchMode === 'semantic'}
              onChange={(e) => setSearchMode(e.target.value)}
            />
            Semantic Search
          </label>
          <label>
            <input
              type="radio"
              value="hybrid"
              checked={searchMode === 'hybrid'}
              onChange={(e) => setSearchMode(e.target.value)}
            />
            Hybrid Search
          </label>
        </div>
        
        {/* Task Filter */}
        <div className="task-filter">
          <select
            value={selectedTaskId}
            onChange={(e) => setSelectedTaskId(e.target.value)}
            className="select-task"
          >
            <option value="">All Documents</option>
            {tasks.map((task) => (
              <option key={task.id} value={task.id}>
                📋 {task.title}
              </option>
            ))}
          </select>
        </div>
        
        {/* Task Documents Preview */}
        {taskDocuments && (
          <div className="task-docs-preview">
            <small>📄 Searching in {taskDocuments.length} task documents</small>
          </div>
        )}
        
        {/* Advanced Filters */}
        <button
          type="button"
          className="btn-filters"
          onClick={() => setExpandedFilters(!expandedFilters)}
        >
          {expandedFilters ? '▼ Hide' : '▶ Show'} Advanced Filters
        </button>
        
        {expandedFilters && (
          <div className="filters-panel">
            <div className="filter-group">
              <label>
                Results per page: <strong>{topK}</strong>
                <input
                  type="range"
                  min="1"
                  max="50"
                  value={topK}
                  onChange={(e) => setTopK(parseInt(e.target.value))}
                />
              </label>
            </div>
            
            <div className="filter-group">
              <label>
                Minimum relevance score: <strong>{minScore.toFixed(2)}</strong>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={minScore}
                  onChange={(e) => setMinScore(parseFloat(e.target.value))}
                />
              </label>
            </div>
            
            <div className="filter-group">
              <label>Sort by:</label>
              <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
                <option value="relevance">Relevance (Default)</option>
                <option value="recency">Recency</option>
                <option value="popularity">Popularity</option>
              </select>
            </div>
            
            {searchMode === 'hybrid' && (
              <>
                <div className="filter-group">
                  <label>
                    Semantic Weight: <strong>{semanticWeight.toFixed(2)}</strong>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.05"
                      value={semanticWeight}
                      onChange={(e) => setSemanticWeight(parseFloat(e.target.value))}
                    />
                  </label>
                </div>
                
                <div className="filter-group">
                  <label>
                    Keyword Weight: <strong>{keywordWeight.toFixed(2)}</strong>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.05"
                      value={keywordWeight}
                      onChange={(e) => setKeywordWeight(parseFloat(e.target.value))}
                    />
                  </label>
                </div>
              </>
            )}
          </div>
        )}
      </form>
      
      {error && <div className="error-box">❌ {error}</div>}
      
      {/* Results Section */}
      <div className="results-panel panel">
        <h3>Results {results.length > 0 && <span>({results.length})</span>}</h3>
        
        {results.length === 0 && query ? (
          <div className="no-results">
            <p>No relevant documents found.</p>
            {metadata && (
              <div className="search-info">
                <p>
                  Highest match score: <strong>{searchAPI.formatScore(metadata.max_score)}</strong> | 
                  Minimum required: <strong>{searchAPI.formatScore(metadata.min_threshold)}</strong>
                </p>
                <p style={{ fontSize: '0.9rem', color: '#5a6a66' }}>
                  Try refining your search with more specific terms or uploading related documents.
                </p>
              </div>
            )}
          </div>
        ) : results.length === 0 ? (
          <p style={{ color: '#666' }}>No results yet. Try searching for something!</p>
        ) : (
          <div className="results-list">
            {results.map((result, idx) => (
              <div key={result.chunk_id} className="result-card">
                <div className="result-header">
                  <div className="result-rank">#{idx + 1}</div>
                  <div className="result-file">
                    <strong>{result.filename}</strong>
                    <span className="result-chunk">Chunk {result.chunk_index}</span>
                  </div>
                  <div
                    className="result-score"
                    style={{ backgroundColor: getScoreColor(result.relevance_score || result.combined_score) }}
                  >
                    <span className="score-label">Relevance</span>
                    <span className="score-value">
                      {searchAPI.formatScore(result.relevance_score || result.combined_score)}
                    </span>
                  </div>
                </div>
                
                <div className="result-body">
                  <p className="result-text">{result.text}</p>
                  
                  <div className="result-meta">
                    <span className="meta-item">
                      👤 <small>{result.uploaded_by}</small>
                    </span>
                    <span className="meta-item">
                      📊 <small>{result.token_count} tokens</small>
                    </span>
                    {metadata?.strategy === 'hybrid-semantic-keyword-rbac' && (
                      <>
                        <span className="meta-item">
                          🧠 <small>Semantic: {searchAPI.formatScore(result.semantic_score)}</small>
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
        
        {/* Metadata Footer */}
        {metadata && results.length > 0 && (
          <div className="search-metadata">
            <div className="metadata-item">
              <small><strong>Model:</strong> {metadata.model_used}</small>
            </div>
            <div className="metadata-item">
              <small><strong>Strategy:</strong> {metadata.strategy}</small>
            </div>
            {metadata.semantic_weight !== undefined && (
              <div className="metadata-item">
                <small>
                  <strong>Weights:</strong> Semantic {(metadata.semantic_weight * 100).toFixed(0)}% + 
                  Keyword {(metadata.keyword_weight * 100).toFixed(0)}%
                </small>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
