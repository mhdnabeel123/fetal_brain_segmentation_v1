import { useState, useEffect } from 'react';
import { FiSun, FiMoon } from 'react-icons/fi';

export default function Header({ darkMode, setDarkMode }) {
  const [scrolled, setScrolled] = useState(false);
  const [showInfo, setShowInfo] = useState(false);

  useEffect(() => {
    const h = () => setScrolled(window.scrollY > 8);
    window.addEventListener('scroll', h);
    return () => window.removeEventListener('scroll', h);
  }, []);

  return (
    <header className="header-wrap" style={{ boxShadow: scrolled ? '0 4px 40px rgba(0,0,0,0.7)' : 'none' }}>
      <div className="header-inner">

        {/* Logo */}
        <button className="logo-btn" onClick={() => setShowInfo(v => !v)} id="logo-btn">
          <div style={{ position: 'relative' }}>
            <div className="logo-icon">
              {/* Brain SVG */}
              <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ width: '1.3rem', height: '1.3rem' }}>
                <path d="M9.5 2a5.5 5.5 0 0 1 5.5 5.5v1a5.5 5.5 0 0 1-5.5 5.5A5.5 5.5 0 0 1 4 8.5v-1A5.5 5.5 0 0 1 9.5 2z" />
                <path d="M14.5 2a5.5 5.5 0 0 1 5.5 5.5v1a5.5 5.5 0 0 1-5.5 5.5" />
                <path d="M12 14v8M8 18h8" />
              </svg>
            </div>
            <div className="logo-dot" />
          </div>
          <div style={{ textAlign: 'left' }}>
            <div className="logo-name gradient-text">NeuroScan AI</div>
            <div className="logo-sub">Fetal Head Segmentation</div>
          </div>
        </button>

        {/* Center meta — desktop */}
        <div className="header-status" style={{ gap: '1.25rem' }}>
          {[
            { label: 'Model', val: 'U-Net++', dot: '#10b981' },
            { label: 'Device', val: 'MPS / GPU', dot: '#3b82f6' },
            { label: 'Classes', val: 'Brain', dot: '#a78bfa' },
          ].map(item => (
            <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.72rem' }}>
              <div style={{ width: '0.4rem', height: '0.4rem', borderRadius: '50%', background: item.dot, animation: 'pulse-dot 2s ease-in-out infinite' }} />
              <span style={{ color: '#475569' }}>{item.label}:</span>
              <span style={{ fontWeight: 700, color: '#c4b5fd' }}>{item.val}</span>
            </div>
          ))}
        </div>

        {/* Right */}
        <div className="header-right">
          <div className="status-pill">
            <div className="status-pill-dot" />
            U-Net++ Active
          </div>
          <button id="theme-toggle" className="icon-btn" onClick={() => setDarkMode(!darkMode)} aria-label="Toggle theme">
            {darkMode
              ? <FiSun style={{ width: '1rem', height: '1rem', color: '#fbbf24' }} />
              : <FiMoon style={{ width: '1rem', height: '1rem' }} />}
          </button>
        </div>
      </div>

      {/* Info drawer */}
      {showInfo && (
        <div className="header-info-drawer">
          <div className="header-info-grid">
            {[
              { label: 'Architecture', val: 'U-Net++ (Nested)' },
              { label: 'Input', val: '256×256 Grayscale' },
              { label: 'Classes', val: 'Background · Brain · CSP · LV' },
              { label: 'Backend', val: 'FastAPI + PyTorch' },
            ].map(item => (
              <div key={item.label} className="info-chip">
                <div className="info-chip-label">{item.label}</div>
                <div className="info-chip-val">{item.val}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </header>
  );
}
