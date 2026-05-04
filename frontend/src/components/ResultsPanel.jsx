import { useState } from 'react';
import { FiDownload, FiLayers, FiMaximize2, FiGrid } from 'react-icons/fi';
import ComparisonSlider from './ComparisonSlider';
import ExplainableAI from './ExplainableAI';
import SpotlightCard from './SpotlightCard';

export default function ResultsPanel({ result, originalPreview }) {
  const [activeView, setActiveView] = useState('grid');
  const [overlayOpacity, setOverlayOpacity] = useState(50);
  const [selectedImage, setSelectedImage] = useState(null);

  if (!result) return null;

  const maskSrc    = `data:image/png;base64,${result.mask}`;
  const overlaySrc = `data:image/png;base64,${result.overlay}`;
  const heatmapSrc = `data:image/png;base64,${result.heatmap}`;

  const downloadImage = (src, filename) => {
    const a = document.createElement('a');
    a.href = src; a.download = filename;
    document.body.appendChild(a); a.click();
    document.body.removeChild(a);
  };
  const downloadAll = () => {
    downloadImage(maskSrc, 'segmentation_mask.png');
    setTimeout(() => downloadImage(overlaySrc, 'overlay.png'), 300);
    setTimeout(() => downloadImage(heatmapSrc, 'heatmap.png'), 600);
  };

  const metrics = [
    { label:'Confidence', value:`${(result.confidence * 100).toFixed(1)}%`, icon:'🎯', color:'#a78bfa', glow:'rgba(167,139,250,0.25)' },
    { label:'Inference',  value:`${result.inference_time_ms.toFixed(0)}ms`, icon:'⚡', color:'#fbbf24', glow:'rgba(251,191,36,0.25)'  },
    { label:'Structures', value:result.detected_structures.length,          icon:'🧬', color:'#34d399', glow:'rgba(52,211,153,0.25)'  },
    { label:'Resolution', value:`${result.image_size.width}×${result.image_size.height}`, icon:'📐', color:'#60a5fa', glow:'rgba(96,165,250,0.25)' },
  ];

  const classColors = { Head:'#ef4444' };
  const structureGradients = {
    Head: 'linear-gradient(90deg,#ef4444,#f87171)',
  };

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:'1.25rem' }} className="animate-slide-up">

      {/* ── Top header bar ── */}
      <div style={{ display:'flex', flexWrap:'wrap', alignItems:'center', justifyContent:'space-between', gap:'0.75rem' }}>
        <div style={{ display:'flex', alignItems:'center', gap:'0.625rem' }}>

          <div className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background:'linear-gradient(135deg,#7c3aed,#2d8bff)' }}>
            <svg viewBox="0 0 24 24" fill="white" className="w-4 h-4">
              <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
            </svg>
          </div>
          <h2 className="text-lg font-black text-surface-100" style={{fontFamily:'Orbitron'}}>
            Analysis Results
          </h2>
          <span className="badge-success text-[10px]">Complete</span>
        </div>        <div style={{ display:'flex', alignItems:'center', gap:'0.5rem' }}>
          {/* View toggle */}
          <div style={{ display:'flex', borderRadius:'0.75rem', overflow:'hidden', border:'1px solid rgba(100,116,139,0.25)', background:'rgba(10,5,25,0.5)' }}>
            {[{id:'grid',icon:<FiGrid style={{width:'0.875rem',height:'0.875rem'}}/>},{id:'compare',icon:<FiLayers style={{width:'0.875rem',height:'0.875rem'}}/>}].map(v => (
              <button key={v.id} onClick={() => setActiveView(v.id)}
                style={{
                  display:'flex', alignItems:'center', gap:'0.375rem',
                  padding:'0.375rem 0.75rem', fontSize:'0.75rem', fontWeight:700,
                  transition:'all 0.2s', border:'none', cursor:'pointer',
                  background: activeView===v.id ? '#7c3aed' : 'transparent',
                  color: activeView===v.id ? 'white' : '#64748b',
                  fontFamily:'Space Grotesk',
                }}
              >
                {v.icon} {v.id.charAt(0).toUpperCase()+v.id.slice(1)}
              </button>
            ))}
          </div>
          <button onClick={downloadAll} id="download-results" className="btn-secondary">
            <FiDownload style={{width:'0.875rem',height:'0.875rem'}} /> Export All
          </button>
        </div>
      </div>

      {/* ── Metrics ── */}
      <div style={{ display:'grid', gridTemplateColumns:'repeat(2,1fr)', gap:'0.75rem' }}>
        {metrics.map((m, i) => (
          <SpotlightCard key={i} spotlightColor={m.glow}
            style={{ padding:'1rem', animationDelay:`${i*0.06}s` }}>
            <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:'0.5rem' }}>
              <span style={{ fontSize:'0.65rem', textTransform:'uppercase', letterSpacing:'0.1em', color:'#64748b', fontWeight:700 }}>{m.label}</span>
              <span style={{ fontSize:'1.25rem' }}>{m.icon}</span>
            </div>
            <p style={{ fontSize:'1.5rem', fontWeight:900, fontFamily:'JetBrains Mono, monospace', color:m.color }}>{m.value}</p>
          </SpotlightCard>
        ))}
      </div>


      {/* ── Visualization ── */}
      {activeView === 'grid' ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            {title:'Original',          src:originalPreview, dl:'original.png'},
            {title:'Segmentation Mask', src:maskSrc,         dl:'segmentation_mask.png'},
            {title:'Overlay',           src:overlaySrc,      dl:'overlay.png'},
            {title:'Confidence Heatmap',src:heatmapSrc,      dl:'heatmap.png'},
          ].map(card => (
            <div key={card.title} className="image-card group" onClick={() => setSelectedImage(card)}>
              <div className="relative aspect-square bg-surface-900">
                <img src={card.src} alt={card.title} className="w-full h-full object-contain" />
                <div className="scan-overlay" />
                <div className="absolute inset-0 bg-gradient-to-t from-surface-950/70 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex gap-1">
                  <button onClick={e => { e.stopPropagation(); setSelectedImage(card); }}
                    className="p-1.5 rounded-lg bg-surface-900/80 text-surface-300 hover:text-white border border-surface-700/50 transition-colors">
                    <FiMaximize2 className="w-3 h-3" />
                  </button>
                  <button onClick={e => { e.stopPropagation(); downloadImage(card.src, card.dl); }}
                    className="p-1.5 rounded-lg bg-surface-900/80 text-surface-300 hover:text-white border border-surface-700/50 transition-colors">
                    <FiDownload className="w-3 h-3" />
                  </button>
                </div>
              </div>
              <div className="px-3 py-2 border-t border-surface-700/30">
                <p className="text-xs font-semibold text-surface-300" style={{fontFamily:'Space Grotesk'}}>{card.title}</p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="glass-card p-4">
          <ComparisonSlider beforeSrc={originalPreview} afterSrc={overlaySrc} beforeLabel="Original" afterLabel="Segmented" />
        </div>
      )}

      {/* ── Overlay control ── */}
      <div className="glass-card p-5">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-lg">🔬</span>
            <span className="text-sm font-bold text-surface-200" style={{fontFamily:'Space Grotesk'}}>Overlay Transparency</span>
          </div>
          <span className="text-xs font-mono font-bold text-violet-400">{overlayOpacity}%</span>
        </div>
        <input type="range" min="0" max="100" value={overlayOpacity}
          onChange={e => setOverlayOpacity(Number(e.target.value))}
          id="opacity-slider"
          className="w-full h-1.5 rounded-full appearance-none cursor-pointer mb-4"
          style={{ accentColor:'#7c3aed', background:`linear-gradient(to right,#7c3aed ${overlayOpacity}%,rgba(100,116,139,0.3) 0)` }}
        />
        <div className="relative rounded-xl overflow-hidden aspect-video bg-surface-900">
          <img src={originalPreview} alt="Original" className="absolute inset-0 w-full h-full object-contain" />
          <img src={overlaySrc} alt="Overlay" className="absolute inset-0 w-full h-full object-contain transition-opacity duration-150"
            style={{ opacity: overlayOpacity / 100 }} />
        </div>
      </div>

      {/* ── Structure confidence bars ── */}
      <div className="glass-card p-5">
        <div className="flex items-center gap-2 mb-5">
          <span className="text-lg">📊</span>
          <h3 className="text-sm font-bold text-surface-200" style={{fontFamily:'Space Grotesk'}}>Structure Confidence Scores</h3>
        </div>
        <div className="space-y-4">
          {Object.entries(result.class_scores)
            .filter(([name]) => name !== 'Background')
            .map(([name, score]) => (
              <div key={name}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: classColors[name] }} />
                    <span className="text-sm font-semibold text-surface-200" style={{fontFamily:'Space Grotesk'}}>{name}</span>
                    {score > 0.85 && <span className="badge-success text-[9px] px-1.5 py-0.5">High</span>}
                    {score > 0 && score <= 0.5 && <span className="badge-warning text-[9px] px-1.5 py-0.5">Low</span>}
                  </div>
                  <span className="text-sm font-black font-mono" style={{ color: classColors[name] }}>
                    {(score * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full h-2 rounded-full bg-surface-800/60 overflow-hidden">
                  <div className="score-bar-fill" style={{ width:`${score*100}%`, background: structureGradients[name] }} />
                </div>
              </div>
            ))}
        </div>

        {/* Legend */}
        <div className="mt-5 pt-4 border-t border-surface-800/50 flex flex-wrap gap-3">
          {Object.entries(classColors).map(([name,color]) => (
            <div key={name} className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor:color }} />
              <span className="text-xs text-surface-400" style={{fontFamily:'Space Grotesk'}}>{name}</span>
            </div>
          ))}
        </div>
      </div>



      {/* ── Fullscreen modal ── */}
      {selectedImage && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background:'rgba(2,6,23,0.95)', backdropFilter:'blur(24px)' }}
          onClick={() => setSelectedImage(null)}
        >
          <div className="max-w-4xl w-full animate-scale-in" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-surface-100" style={{fontFamily:'Orbitron'}}>{selectedImage.title}</h3>
              <button onClick={() => setSelectedImage(null)}
                className="p-2 rounded-xl hover:bg-surface-800 text-surface-400 hover:text-surface-100 transition-colors border border-surface-700/40">
                ✕
              </button>
            </div>
            <div className="glass-card overflow-hidden">
              <img src={selectedImage.src} alt={selectedImage.title} className="w-full rounded-xl" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
