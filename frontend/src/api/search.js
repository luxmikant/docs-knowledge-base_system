import api from './client';

// Search operations
export const search = (query, topK = 10, minScore = 0.3) =>
  api.post('/search', { query, top_k: topK, min_score: minScore });

export const hybridSearch = (query, topK = 10, minScore = 0.3, semanticWeight = 0.7, keywordWeight = 0.3) =>
  api.post('/search/hybrid', {
    query,
    top_k: topK,
    min_score: minScore,
    semantic_weight: semanticWeight,
    keyword_weight: keywordWeight,
  });

export const taskAwareSearch = (query, taskId, topK = 10, minScore = 0.3) =>
  api.post('/search', { query, top_k: topK, min_score: minScore, task_id: taskId });

// Task document operations
export const addDocumentsToTask = (taskId, documentIds) =>
  api.post('/tasks/documents/add', { task_id: taskId, document_ids: documentIds });

export const getTaskDocuments = (taskId) =>
  api.get(`/tasks/${taskId}/documents`);

// Index optimization (admin only)
export const batchIndexDocuments = (documentIds, forceRebuild = false) =>
  api.post('/admin/index/batch', { document_ids: documentIds, force_rebuild: forceRebuild });

export const getIndexStats = () =>
  api.get('/admin/index/stats');

export const optimizeIndex = () =>
  api.post('/admin/index/optimize');

export const rebuildSearchIndex = () =>
  api.post('/admin/index/rebuild');

// Utility functions
export const formatScore = (score, decimals = 3) => {
  if (!score && score !== 0) return 'N/A';
  return parseFloat(score).toFixed(decimals);
};

export const formatBytes = (bytes) => {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};
