import { useState, useEffect } from 'react';
import toast, { Toaster } from 'react-hot-toast';
import Header from './components/Header';
import ImageUpload from './components/ImageUpload';
import ResultsPanel from './components/ResultsPanel';
import ExplainableAI from './components/ExplainableAI';
import Aurora from './components/Aurora';
import SpotlightCard from './components/SpotlightCard';
import ShinyText from './components/ShinyText';
import { predictImage } from './services/api';
import { FiShield, FiCpu, FiZap, FiGitBranch } from 'react-icons/fi';

export default function App() {
  const [darkMode, setDarkMode] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [originalPreview, setOriginalPreview] = useState(null);
  const [history, setHistory] = useState([]);

  const handleUpload = async (file) => {
    setIsLoading(true);
    setResult(null);
    const preview = URL.createObjectURL(file);
    setOriginalPreview(preview);

    const loadingToast = toast.loading('🧠 Analyzing fetal ultrasound…', {
      style: { background: '#0a050f', color: '#e2e8f0', border: '1px solid rgba(124,58,237,0.35)', borderRadius: '0.875rem' },
    });

    try {
      const response = await predictImage(file);
      setResult(response);
      setHistory(prev => [{
        id: Date.now(), filename: file.name,
        result: response, preview,
        timestamp: new Date().toLocaleTimeString(),
      }, ...prev]);
      toast.success(`✅ ${response.detected_structures.length} structure${response.detected_structures.length !== 1 ? 's' : ''} detected`, {
        duration: 4000,
        style: { background: '#0a050f', color: '#6ee7b7', border: '1px solid rgba(16,185,129,0.3)', borderRadius: '0.875rem' },
      });
    } catch (error) {
      toast.error(`❌ ${error.message || 'Analysis failed'}`, {
        duration: 6000,
        style: { background: '#0a050f', color: '#fca5a5', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '0.875rem' },
      });
    } finally {
      setIsLoading(false);
      toast.dismiss(loadingToast);
    }
  };

  return (
    <div className={darkMode ? 'dark' : ''}>
      <div className="app-root">
        <Toaster position="top-right" />

        {/* ── Global Aurora background ── */}
        <div className="aurora-bg-wrap">
          <Aurora
            colorStops={['#3b0df5', '#7c3aed', '#05c8ad']}
            amplitude={1.0}
            blend={0.45}
            speed={0.8}
          />
        </div>

        {/* ── Subtle particle dots layer ── */}
        <ParticleDots />

        <Header darkMode={darkMode} setDarkMode={setDarkMode} />

        <main className="main-container">

          {/* ── Hero ── */}
          {!result && !isLoading && (
            <div className="hero-section animate-slide-up">
              {/* Pill badge */}
              <div className="hero-badge">
                <span className="hero-badge-dot" />
                <ShinyText
                  text="AI-Powered Fetal Neurosonology"
                  color="#a78bfa"
                  shineColor="#f0e6ff"
                  speed={4}
                  className="hero-badge-text"
                />
              </div>

              {/* Headline */}
              <h2 className="hero-title">
                <span className="gradient-text" style={{ fontFamily: 'Orbitron, sans-serif', display: 'block' }}>
                  NeuroScan AI
                </span>
                <span className="hero-subtitle-line">Fetal Head Segmentation</span>
              </h2>

              <p className="hero-desc">
                Upload a fetal ultrasound image for instant, high-precision head circumference
                segmentation powered by U‑Net++ deep learning.
              </p>

              {/* Feature cards using SpotlightCard */}
              <div className="feature-grid">
                {[
                  { icon: FiCpu,       label: 'U-Net++ Model',  desc: 'Nested architecture',     color: '#3b82f6', glow: 'rgba(59,130,246,0.3)' },
                  { icon: FiZap,       label: 'Real-time',      desc: '< 100ms inference',       color: '#f59e0b', glow: 'rgba(245,158,11,0.3)' },
                  { icon: FiGitBranch, label: 'Precise',        desc: 'Single-class focus',      color: '#10b981', glow: 'rgba(16,185,129,0.3)' },
                  { icon: FiShield,    label: 'Verified',       desc: 'Research tool',           color: '#a78bfa', glow: 'rgba(167,139,250,0.3)' },
                ].map((feat, i) => (
                  <SpotlightCard
                    key={i}
                    spotlightColor={feat.glow}
                    className="feature-card"
                    style={{ animationDelay: `${i * 0.08}s` }}
                  >
                    <div className="feature-icon-wrap" style={{ background: `${feat.color}18`, border: `1px solid ${feat.color}40` }}>
                      <feat.icon style={{ color: feat.color, width: '1.2rem', height: '1.2rem' }} />
                    </div>
                    <p className="feature-label">{feat.label}</p>
                    <p className="feature-desc">{feat.desc}</p>
                  </SpotlightCard>
                ))}
              </div>
            </div>
          )}

          {/* ── Main content grid ── */}
          <div className={`content-grid ${result ? 'content-grid-results' : 'content-grid-upload'}`}>
            {/* Left panel */}
            <div className="left-panel">
              <SpotlightCard spotlightColor="rgba(124,58,237,0.15)" className="upload-card-wrap">
                <ImageUpload
                  onUpload={handleUpload}
                  isLoading={isLoading}
                  uploadedFiles={uploadedFiles}
                  setUploadedFiles={setUploadedFiles}
                />
              </SpotlightCard>

              {/* AI Assistant - Left Panel */}
              {result && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '0.25rem' }}>
                  <ExplainableAI result={result} />
                </div>
              )}

              {/* Analysis history */}
              {history.length > 1 && (
                <div className="glass-card history-card animate-slide-up">
                  <p className="history-title">Recent Analyses</p>
                  <div className="history-list">
                    {history.slice(0, 6).map(item => (
                      <button
                        key={item.id}
                        onClick={() => { setResult(item.result); setOriginalPreview(item.preview); }}
                        className="history-item"
                      >
                        <img src={item.preview} alt="" className="history-thumb" />
                        <div className="history-info">
                          <p className="history-name">{item.filename}</p>
                          <p className="history-time">{item.timestamp}</p>
                        </div>
                        <span className="history-conf">{(item.result.confidence * 100).toFixed(0)}%</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Right panel */}
            {(result || isLoading) && (
              <div className="right-panel">
                {isLoading ? <LoadingState /> : (
                  <ResultsPanel result={result} originalPreview={originalPreview} />
                )}
              </div>
            )}
          </div>
        </main>

        {/* Footer */}
        <footer className="app-footer">
          <p className="footer-left">© 2025 NeuroScan AI — Fetal Head Segmentation Platform</p>
          <div className="footer-right">
            <span className="footer-dot" />
            <p className="footer-text">
              Powered by <span style={{ color: '#a78bfa', fontWeight: 700 }}>U-Net++</span> · PyTorch · FastAPI · Ollama
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
}

/* ── Particle dot layer ── */
function ParticleDots() {
  useEffect(() => {
    const canvas = document.getElementById('rb-particles');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let W = canvas.width = window.innerWidth;
    let H = canvas.height = window.innerHeight;
    const pts = Array.from({ length: 60 }, () => ({
      x: Math.random() * W, y: Math.random() * H,
      r: Math.random() * 1.2 + 0.3,
      dx: (Math.random() - 0.5) * 0.3,
      dy: (Math.random() - 0.5) * 0.3,
      a: Math.random() * 0.5 + 0.1,
    }));
    let raf;
    const draw = () => {
      ctx.clearRect(0, 0, W, H);
      pts.forEach(p => {
        p.x = (p.x + p.dx + W) % W;
        p.y = (p.y + p.dy + H) % H;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(167,139,250,${p.a})`;
        ctx.fill();
      });
      raf = requestAnimationFrame(draw);
    };
    draw();
    const onResize = () => { W = canvas.width = window.innerWidth; H = canvas.height = window.innerHeight; };
    window.addEventListener('resize', onResize);
    return () => { cancelAnimationFrame(raf); window.removeEventListener('resize', onResize); };
  }, []);
  return <canvas id="rb-particles" style={{ position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 0, opacity: 0.35 }} />;
}

/* ── Loading state ── */
function LoadingState() {
  const [step, setStep] = useState(0);
  const steps = ['Preprocessing image', 'Running U-Net++ inference', 'Generating visualizations', 'Building clinical report'];

  useEffect(() => {
    const id = setInterval(() => setStep(s => Math.min(s + 1, steps.length - 1)), 850);
    return () => clearInterval(id);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="glass-card loading-card animate-scale-in">
      <div className="loading-inner">
        {/* Scanner rings */}
        <div className="scanner-wrap">
          {[0, 1, 2].map(i => (
            <div key={i} className="scanner-ring"
              style={{ inset: `${i * 10}px`, animationDelay: `${i * 0.25}s`, animationDuration: `${1.5 + i * 0.4}s` }} />
          ))}
          <div className="scanner-spin outer" />
          <div className="scanner-spin inner" />
          <div className="scanner-center">🧠</div>
          {/* Scan line */}
          <div className="scanner-scanline" />
        </div>

        <h3 className="loading-title">Analyzing Ultrasound</h3>
        <p className="loading-desc">U-Net++ is segmenting the fetal head circumference…</p>

        <div className="loading-steps">
          {steps.map((s, i) => (
            <div key={i} className="loading-step">
              <div className={`step-dot ${i < step ? 'done' : i === step ? 'active' : 'idle'}`}>
                {i < step ? (
                  <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" className="step-check">
                    <polyline points="5 13 9 17 19 7"/>
                  </svg>
                ) : i === step ? <div className="step-pulse" /> : null}
              </div>
              <span className={`step-label ${i <= step ? 'step-active' : 'step-inactive'}`}>{s}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
