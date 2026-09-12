import { useState, useRef } from 'react';
import './UploadPage.css';

function UploadPage() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef(null);

  function applyFile(selectedFile) {
    if (!selectedFile) return;
    if (!selectedFile.type.match(/image\/(jpeg|png)/)) {
      alert('Please select a JPG or PNG image file.');
      return;
    }
    setFile(selectedFile);
    setPreview(URL.createObjectURL(selectedFile));
  }

  function handleFileChange(e) {
    applyFile(e.target.files[0]);
  }

  function handleDragOver(e) {
    e.preventDefault();
    setIsDragging(true);
  }

  function handleDragLeave() {
    setIsDragging(false);
  }

  function handleDrop(e) {
    e.preventDefault();
    setIsDragging(false);
    applyFile(e.dataTransfer.files[0]);
  }

  function handleProcess() {
    if (!file) return;
    console.log('Would send to OCR:', file.name);
    alert('OCR pipeline coming soon');
  }

  function formatSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  }

  return (
    <div className="upload-page">
      <div className="upload-card">
        <h1 className="upload-heading">Upload Prescription</h1>

        {/* Drop zone */}
        <div
          className={`drop-zone ${isDragging ? 'drop-zone--active' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => inputRef.current.click()}
          role="button"
          tabIndex={0}
          aria-label="File drop zone"
          onKeyDown={(e) => e.key === 'Enter' && inputRef.current.click()}
        >
          <input
            ref={inputRef}
            id="file-input"
            type="file"
            accept="image/jpeg,image/png"
            className="file-input-hidden"
            onChange={handleFileChange}
          />

          {preview ? (
            <div className="preview-wrapper" onClick={(e) => e.stopPropagation()}>
              <img
                src={preview}
                alt="Prescription preview"
                className="preview-image"
              />
            </div>
          ) : (
            <div className="drop-zone-placeholder">
              <svg className="upload-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
              <p className="drop-zone-text">
                Drag &amp; drop a prescription image here
              </p>
              <p className="drop-zone-subtext">JPG or PNG only</p>
            </div>
          )}
        </div>

        {/* Browse button */}
        <button
          id="browse-btn"
          className="browse-btn"
          onClick={() => inputRef.current.click()}
          type="button"
        >
          Browse Files
        </button>

        {/* File info */}
        {file && (
          <div className="file-info">
            <span className="file-name">{file.name}</span>
            <span className="file-size">{formatSize(file.size)}</span>
          </div>
        )}

        {/* Process button */}
        <button
          id="process-btn"
          className="process-btn"
          disabled={!file}
          onClick={handleProcess}
          type="button"
        >
          Process Prescription
        </button>
      </div>
    </div>
  );
}

export default UploadPage;
