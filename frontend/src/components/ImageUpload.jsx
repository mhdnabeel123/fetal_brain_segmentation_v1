import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { FiX, FiZap } from 'react-icons/fi';

export default function ImageUpload({ onUpload, isLoading, uploadedFiles, setUploadedFiles }) {
  const [hovering, setHovering] = useState(false);

  const onDrop = useCallback((acceptedFiles) => {
    const newFiles = acceptedFiles.map(file => ({
      file, preview: URL.createObjectURL(file),
      name: file.name, size: (file.size / 1024).toFixed(1),
    }));
    setUploadedFiles(prev => [...prev, ...newFiles]);
  }, [setUploadedFiles]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'] },
    multiple: false,
    disabled: isLoading,
  });

  const removeFile = (idx) => {
    setUploadedFiles(prev => {
      const u = [...prev];
      URL.revokeObjectURL(u[idx].preview);
      u.splice(idx, 1);
      return u;
    });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }} className="animate-slide-up">
      {/* Drop zone */}
      <div
        {...getRootProps()}
        id="upload-dropzone"
        onMouseEnter={() => setHovering(true)}
        onMouseLeave={() => setHovering(false)}
        className={`upload-zone ${isDragActive ? 'drag-active' : ''} ${isLoading ? 'opacity-50 pointer-events-none' : ''}`}
      >
        <input {...getInputProps()} />
        <div className="upload-zone-grid" />

        <div className="upload-zone-inner">
          {/* Icon */}
          <div className={`upload-icon-ring ${isDragActive || hovering ? 'animate-float' : ''}`}
            style={{ boxShadow: hovering || isDragActive ? '0 0 40px rgba(124,58,237,0.3), 0 0 80px rgba(124,58,237,0.12)' : 'none' }}>
            {/* Ultrasound icon */}
            <svg viewBox="0 0 24 24" fill="none" stroke="#a78bfa" strokeWidth="1.5"
              strokeLinecap="round" strokeLinejoin="round" style={{ width: '2.5rem', height: '2.5rem' }}>
              <rect x="3" y="3" width="18" height="18" rx="3"/>
              <path d="M9 8v8M12 6v12M15 9v6"/>
            </svg>
            <div className="upload-icon-badge">
              <svg viewBox="0 0 24 24" fill="white" style={{ width: '0.875rem', height: '0.875rem' }}>
                <path d="M12 2a10 10 0 11-5 18.66L4 21l.34-3A10 10 0 0112 2z"/>
              </svg>
            </div>
          </div>

          <h3 className="upload-title">
            {isDragActive ? '🎯 Drop it right here!' : 'Upload Ultrasound Image'}
          </h3>
          <p className="upload-desc">Drag &amp; drop a fetal ultrasound image or click to browse.</p>
          <p className="upload-hint">PNG, JPG, BMP, TIFF — Max 20MB</p>

          <button type="button" className="upload-browse-btn">Browse Files</button>
        </div>

        {/* Scan line when dragging */}
        {isDragActive && (
          <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', borderRadius: 'inherit', pointerEvents: 'none' }}>
            <div style={{
              position: 'absolute', left: 0, right: 0, height: '2px',
              background: 'linear-gradient(90deg, transparent, #7c3aed, #2d8bff, transparent)',
              animation: 'scan-line 2s linear infinite',
            }} />
          </div>
        )}
      </div>

      {/* Previews */}
      {uploadedFiles.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }} className="animate-scale-in">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
              Selected ({uploadedFiles.length})
            </span>
            <button
              onClick={() => { uploadedFiles.forEach(f => URL.revokeObjectURL(f.preview)); setUploadedFiles([]); }}
              style={{ fontSize: '0.72rem', color: '#475569', background: 'none', border: 'none', cursor: 'pointer', transition: 'color 0.2s' }}
              onMouseEnter={e => e.target.style.color = '#fca5a5'}
              onMouseLeave={e => e.target.style.color = '#475569'}
            >Clear all</button>
          </div>

          <div className="file-preview-grid">
            {uploadedFiles.map((file, idx) => (
              <div key={idx} className="file-preview-item">
                <img src={file.preview} alt={file.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                <div className="file-overlay" />
                <div className="file-overlay-info">
                  <div className="file-name">{file.name}</div>
                  <div className="file-size">{file.size} KB</div>
                </div>
                <button className="file-remove-btn" onClick={e => { e.stopPropagation(); removeFile(idx); }}>
                  <FiX style={{ width: '0.75rem', height: '0.75rem' }} />
                </button>
              </div>
            ))}
          </div>

          {/* Analyze */}
          <button
            id="analyze-button"
            className="analyze-btn"
            onClick={() => onUpload(uploadedFiles[0].file)}
            disabled={isLoading}
          >
            {isLoading ? (
              <><div className="btn-spinner" /> Analyzing…</>
            ) : (
              <><FiZap style={{ width: '1rem', height: '1rem' }} /> Analyze with AI <span style={{ fontSize: '1rem' }}>✨</span></>
            )}
          </button>
        </div>
      )}
    </div>
  );
}
