import { useState } from 'react';
import api from '../api/client';

export default function DocumentUploadForm({ onUploadSuccess, onError }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    // Validate file type
    const validTypes = ['.txt', '.pdf'];
    const fileExtension = '.' + selectedFile.name.split('.').pop().toLowerCase();
    
    if (!validTypes.includes(fileExtension)) {
      setErrorMsg('Only .txt and .pdf files are supported');
      setFile(null);
      return;
    }

    // Validate file size (max 10MB)
    const maxSizeMB = 10;
    if (selectedFile.size > maxSizeMB * 1024 * 1024) {
      setErrorMsg(`File size exceeds ${maxSizeMB}MB limit`);
      setFile(null);
      return;
    }

    setErrorMsg('');
    setFile(selectedFile);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setErrorMsg('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post('/documents', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      
      // Reset form
      setFile(null);
      e.target.reset();
      
      // Notify parent component
      onUploadSuccess?.(response.data);
    } catch (err) {
      const errorMessage = err?.response?.data?.error || 'Failed to upload document';
      setErrorMsg(errorMessage);
      onError?.(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  return (
    <form className="document-upload-form panel" onSubmit={handleSubmit}>
      <h3>Upload Document</h3>
      
      {errorMsg && <div className="error-box">{errorMsg}</div>}

      <div className="upload-input-group">
        <input
          type="file"
          accept=".txt,.pdf"
          onChange={handleFileChange}
          disabled={uploading}
          required
        />
        <span className="file-info">
          {file ? (
            <>
              <strong>Selected:</strong> {file.name} ({(file.size / 1024).toFixed(2)} KB)
            </>
          ) : (
            'Supported formats: .txt, .pdf (Max 10MB)'
          )}
        </span>
      </div>

      <button type="submit" disabled={!file || uploading}>
        {uploading ? 'Uploading...' : 'Upload'}
      </button>
    </form>
  );
}
