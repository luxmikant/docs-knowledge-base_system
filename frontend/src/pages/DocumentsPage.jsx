import { useEffect, useState } from 'react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function DocumentsPage() {
  const { isAdmin } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [file, setFile] = useState(null);
  const [error, setError] = useState('');

  const fetchDocuments = async () => {
    setLoading(true);
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

  const uploadDocument = async (event) => {
    event.preventDefault();
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      await api.post('/documents', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setFile(null);
      fetchDocuments();
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to upload document');
    }
  };

  return (
    <section>
      <h2>Documents</h2>

      {isAdmin && (
        <form className="panel" onSubmit={uploadDocument}>
          <h3>Upload .txt Document</h3>
          <input type="file" accept=".txt" onChange={(e) => setFile(e.target.files?.[0] || null)} required />
          <button type="submit">Upload</button>
        </form>
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
                <div>
                  <h4>{doc.filename}</h4>
                  <small>
                    Uploaded by: {doc.uploaded_by_username} | Size: {doc.file_size} bytes
                  </small>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
