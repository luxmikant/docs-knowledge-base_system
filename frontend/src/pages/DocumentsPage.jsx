import { useEffect, useState } from 'react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import DocumentUploadForm from '../components/DocumentUploadForm';
import DocumentViewModal from '../components/DocumentViewModal';
import ConfirmDialog from '../components/ConfirmDialog';

export default function DocumentsPage() {
  const { isAdmin } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [viewingDocument, setViewingDocument] = useState(null);
  const [deletingDocument, setDeletingDocument] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const fetchDocuments = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get('/documents');
      setDocuments(response.data.documents || []);
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleUploadSuccess = () => {
    fetchDocuments();
    setError('');
  };

  const handleUploadError = (err) => {
    setError(err);
  };

  const handleDeleteDocument = async () => {
    if (!deletingDocument) return;

    setDeleting(true);
    try {
      await api.delete(`/documents/${deletingDocument.id}`);
      setDeletingDocument(null);
      fetchDocuments();
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to delete document');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <section>
      <h2>Documents</h2>

      {isAdmin && (
        <DocumentUploadForm 
          onUploadSuccess={handleUploadSuccess}
          onError={handleUploadError}
        />
      )}

      {error && <div className="error-box">{error}</div>}

      <div className="panel">
        <h3>Document Library</h3>
        {loading ? (
          <p>Loading documents...</p>
        ) : documents.length === 0 ? (
          <p>No documents uploaded yet.</p>
        ) : (
          <div className="list">
            {documents.map((doc) => (
              <article className="list-item" key={doc.id}>
                <div className="list-item-content">
                  <div>
                    <h4>{doc.filename}</h4>
                    <small>
                      Uploaded by: {doc.uploaded_by_username} | 
                      Size: {(doc.file_size / 1024).toFixed(2)} KB |
                      Type: {doc.filename.split('.').pop().toUpperCase()}
                    </small>
                  </div>
                </div>
                <div className="list-item-actions">
                  <button 
                    className="btn-secondary"
                    onClick={() => setViewingDocument(doc)}
                  >
                    View
                  </button>
                  {isAdmin && (
                    <button 
                      className="btn-danger"
                      onClick={() => setDeletingDocument(doc)}
                    >
                      Delete
                    </button>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </div>

      <DocumentViewModal 
        document={viewingDocument}
        isOpen={!!viewingDocument}
        onClose={() => setViewingDocument(null)}
      />

      <ConfirmDialog
        isOpen={!!deletingDocument}
        title="Delete Document"
        message={`Are you sure you want to delete "${deletingDocument?.filename}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        isDestructive={true}
        onConfirm={handleDeleteDocument}
        onCancel={() => setDeletingDocument(null)}
      />
    </section>
  );
}
