import { useEffect, useState } from 'react';
import api from '../api/client';

export default function DocumentViewModal({ document, isOpen, onClose }) {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isOpen || !document) return;

    const fetchContent = async () => {
      setLoading(true);
      setError('');
      try {
        // Fetch the document detail endpoint which includes content_text
        const response = await api.get(`/documents/${document.id}`);
        setContent(response.data.content_text || '');
      } catch (err) {
        setError(err?.response?.data?.error || 'Failed to load document content');
      } finally {
        setLoading(false);
      }
    };

    fetchContent();
  }, [document, isOpen]);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{document?.filename}</h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          {loading && <p className="loading">Loading document...</p>}
          
          {error && <div className="error-box">{error}</div>}
          
          {!loading && content && (
            <div className="document-content">
              <p>
                <small>
                  File type: {document?.filename.split('.').pop().toUpperCase()} | 
                  Size: {(document?.file_size / 1024).toFixed(2)} KB |
                  Uploaded by: {document?.uploaded_by_username}
                </small>
              </p>
              <pre>{content}</pre>
            </div>
          )}

          {!loading && !error && !content && <p>No content available</p>}
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}
