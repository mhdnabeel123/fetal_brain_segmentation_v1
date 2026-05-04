import { useState } from 'react';

const structureInfo = {
  Head: {
    color:'#ef4444', bg:'rgba(239,68,68,0.1)', border:'rgba(239,68,68,0.25)',
    icon:'🧠',
    desc:'Primary fetal head circumference — main tissue region of the developing head.',
    normal:'Normally represents the largest region detected.',
  },
};

export default function ExplainableAI({ result }) {
  const [expanded, setExpanded] = useState(true);
  if (!result) return null;

  const { detected_structures, class_scores, confidence } = result;
  const hasStructures = detected_structures.length > 0;

  return (
    <div className="glass-card overflow-hidden animate-slide-up">
      {/* Header */}
      <button
        onClick={() => setExpanded(v => !v)}
        id="explainable-ai-toggle"
        className="w-full flex items-center justify-between p-5 hover:bg-violet-500/5 transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{ background:'linear-gradient(135deg,rgba(124,58,237,0.3),rgba(45,139,255,0.2))', border:'1px solid rgba(124,58,237,0.3)' }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="#a78bfa" strokeWidth="1.8"
              strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
          </div>
          <div>
            <h3 className="text-sm font-bold text-surface-100" style={{fontFamily:'Space Grotesk'}}>Explainable AI Insights</h3>
            <p className="text-xs text-surface-500">Clinical interpretation of segmentation results</p>
          </div>
        </div>
        <div style={{ transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)', transition:'transform 0.3s', color:'#64748b' }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>
      </button>

      {expanded && (
        <div className="px-5 pb-5 space-y-4 animate-slide-up">
          {/* Overall status */}
          <div className={`flex items-start gap-3 p-4 rounded-xl ${hasStructures
              ? 'bg-emerald-500/8 border border-emerald-500/20'
              : 'bg-amber-500/8 border border-amber-500/20'}`}>
            <span className="text-2xl mt-0.5">{hasStructures ? '✅' : '⚠️'}</span>
            <div>
              <p className={`text-sm font-bold ${hasStructures ? 'text-emerald-300' : 'text-amber-300'}`}
                style={{fontFamily:'Space Grotesk'}}>
                {hasStructures
                  ? `${detected_structures.length} head structure${detected_structures.length > 1 ? 's' : ''} detected with high confidence`
                  : 'No significant structures detected'}
              </p>
              <p className="text-xs text-surface-400 mt-0.5">
                Overall model confidence: <span className="font-bold text-violet-400">{(confidence * 100).toFixed(1)}%</span>
              </p>
            </div>
          </div>

          {/* Structure detail cards */}
          {hasStructures && (
            <div className="space-y-3">
              {detected_structures.map(struct => {
                const info = structureInfo[struct];
                if (!info) return null;
                const score = class_scores[struct] || 0;
                return (
                  <div key={struct}
                    className="p-4 rounded-xl transition-all duration-300 hover:scale-[1.01] cursor-default"
                    style={{ background:info.bg, border:`1px solid ${info.border}` }}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xl">{info.icon}</span>
                        <span className="text-sm font-bold text-surface-100" style={{fontFamily:'Space Grotesk'}}>{struct}</span>
                        <span className="w-2 h-2 rounded-full" style={{ backgroundColor:info.color }} />
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-20 rounded-full bg-surface-800/50 overflow-hidden">
                          <div className="h-full rounded-full" style={{ width:`${score*100}%`, backgroundColor:info.color }} />
                        </div>
                        <span className="text-xs font-black font-mono" style={{ color:info.color }}>
                          {(score * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    <p className="text-xs text-surface-400 leading-relaxed" style={{fontFamily:'Space Grotesk'}}>{info.desc}</p>
                    <p className="text-[10px] text-surface-500 mt-1 italic">{info.normal}</p>
                  </div>
                );
              })}
            </div>
          )}

          {/* Color legend */}
          <div className="p-3 rounded-xl border border-surface-700/30" style={{ background:'rgba(15,23,42,0.4)' }}>
            <p className="text-[10px] font-bold text-surface-500 uppercase tracking-wider mb-2" style={{fontFamily:'Space Grotesk'}}>Segmentation Colour Legend</p>
            <div className="flex flex-wrap gap-4">
              {Object.entries(structureInfo).map(([name, info]) => (
                <div key={name} className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-sm" style={{ backgroundColor:info.color }} />
                  <span className="text-xs text-surface-300 font-semibold" style={{fontFamily:'Space Grotesk'}}>{name}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Disclaimer */}
          <div className="flex items-start gap-2 p-3 rounded-xl" style={{ background:'rgba(245,158,11,0.05)', border:'1px solid rgba(245,158,11,0.1)' }}>
            <span className="text-sm mt-0.5">⚠️</span>
            <p className="text-[11px] text-surface-500 leading-relaxed" style={{fontFamily:'Space Grotesk'}}>
              This AI-assisted analysis is for research and educational use only. Clinical decisions must always be made by qualified medical professionals. Not FDA-approved for diagnostic use.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
