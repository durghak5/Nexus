import { useState } from 'react';
import './UploadPage.css';

function UploadPage() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFile = (selectedFile) => {
    if (!selectedFile) return;
    if (!selectedFile.type.startsWith('image/')) {
      setError('Please select an image file');
      return;
    }
    setFile(selectedFile);
    setPreview(URL.createObjectURL(selectedFile));
    setResult(null);
    setError(null);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files[0];
    handleFile(dropped);
  };

  const handleSubmit = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('http://localhost:8000/api/v1/ocr/process', {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
  };

  return (
    <div className="upload-page">
      <h1>Upload Prescription</h1>
      <p className="subtitle">
        Upload a handwritten prescription image. Our OCR model will extract drug names and suggest alternatives.
      </p>

      {!result && (
        <>
          <div
            className={`drop-zone ${preview ? 'has-preview' : ''}`}
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => document.getElementById('file-input').click()}
          >
            {preview ? (
              <img src={preview} alt="Preview" className="preview-img" />
            ) : (
              <div className="drop-content">
                <div className="drop-icon">📤</div>
                <p><strong>Drag & drop</strong> a prescription image here</p>
                <p>or click to browse</p>
              </div>
            )}
            <input
              id="file-input"
              type="file"
              accept="image/*"
              onChange={(e) => handleFile(e.target.files[0])}
              style={{ display: 'none' }}
            />
          </div>

          {file && (
            <div className="file-info">
              <span>{file.name} ({(file.size / 1024).toFixed(1)} KB)</span>
              <button className="btn-secondary" onClick={reset}>Remove</button>
            </div>
          )}

          <div className="actions">
            <button
              className="btn-primary"
              onClick={handleSubmit}
              disabled={!file || loading}
            >
              {loading ? 'Processing...' : 'Process Prescription'}
            </button>
          </div>

          {error && <div className="error-box">❌ {error}</div>}

          {loading && (
            <div className="loading-box">
              🔍 Running OCR, extracting drugs, and finding alternatives... This may take 20-30 seconds.
            </div>
          )}
        </>
      )}

      {result && (
        <div className="results">
          <div className="results-header">
            <h2>📋 Results</h2>
            <button className="btn-secondary" onClick={reset}>Process another</button>
          </div>

          <div className="summary">
            <div className="summary-item">
              <span className="summary-label">Text regions detected</span>
              <span className="summary-value">{result.total_detected}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Drug names extracted</span>
              <span className="summary-value">{result.total_drugs}</span>
            </div>
          </div>

          {result.total_drugs === 0 && (
            <div className="no-results">
              ⚠️ No drug names matched the dictionary. Try a clearer image.
            </div>
          )}

          {result.drugs.map((drug, idx) => (
            <div key={idx} className="drug-card">
              <div className="drug-header">
                <h3>💊 {drug.name}</h3>
                <span className="confidence-badge">
                  {Math.round(drug.confidence * 100)}% confident
                </span>
              </div>
              <div className="drug-meta">
                <span>Raw OCR: <em>{drug.raw_text}</em></span>
                <span>Match: {drug.source}</span>
              </div>

              {drug.recommendations.length > 0 ? (
                <>
                  <h4>Alternative brands (same composition):</h4>
                  <ul className="alt-list">
                    {drug.recommendations.map((alt, i) => (
                      <li key={i}>
                        <span className="alt-name">{alt.brand_name}</span>
                        <span className="alt-match">{alt.composition_match}% match</span>
                      </li>
                    ))}
                  </ul>
                </>
              ) : (
                <p className="no-alt">No alternatives found in the database.</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default UploadPage;