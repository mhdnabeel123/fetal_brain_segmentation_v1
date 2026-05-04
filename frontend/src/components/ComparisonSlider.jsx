import { useState, useRef, useCallback, useEffect } from 'react';
import { FiChevronLeft, FiChevronRight } from 'react-icons/fi';

export default function ComparisonSlider({ beforeSrc, afterSrc, beforeLabel = 'Before', afterLabel = 'After' }) {
  const [position, setPosition] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef(null);

  const updatePosition = useCallback((clientX) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    const percent = Math.max(0, Math.min(100, (x / rect.width) * 100));
    setPosition(percent);
  }, []);

  const handleMouseDown = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
    updatePosition(e.clientX);
  }, [updatePosition]);

  const handleMouseMove = useCallback((e) => {
    if (isDragging) {
      updatePosition(e.clientX);
    }
  }, [isDragging, updatePosition]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleTouchStart = useCallback((e) => {
    setIsDragging(true);
    updatePosition(e.touches[0].clientX);
  }, [updatePosition]);

  const handleTouchMove = useCallback((e) => {
    if (isDragging) {
      updatePosition(e.touches[0].clientX);
    }
  }, [isDragging, updatePosition]);

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.addEventListener('touchmove', handleTouchMove);
      document.addEventListener('touchend', handleMouseUp);
    }
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleMouseUp);
    };
  }, [isDragging, handleMouseMove, handleMouseUp, handleTouchMove]);

  return (
    <div
      ref={containerRef}
      className="comparison-slider relative w-full aspect-square sm:aspect-video rounded-xl overflow-hidden select-none"
      onMouseDown={handleMouseDown}
      onTouchStart={handleTouchStart}
      id="comparison-slider"
    >
      {/* After (full width background) */}
      <div className="absolute inset-0">
        <img
          src={afterSrc}
          alt={afterLabel}
          className="w-full h-full object-contain bg-surface-800"
          draggable={false}
        />
      </div>

      {/* Before (clipped) */}
      <div
        className="absolute inset-0"
        style={{ clipPath: `inset(0 ${100 - position}% 0 0)` }}
      >
        <img
          src={beforeSrc}
          alt={beforeLabel}
          className="w-full h-full object-contain bg-surface-800"
          draggable={false}
        />
      </div>

      {/* Slider line */}
      <div
        className="absolute top-0 bottom-0 w-[3px] z-10"
        style={{ left: `${position}%`, transform: 'translateX(-50%)' }}
      >
        <div className="w-full h-full bg-gradient-to-b from-primary-400 via-accent-400 to-primary-400 shadow-lg shadow-primary-500/30" />
      </div>

      {/* Slider handle */}
      <div
        className="absolute z-20 cursor-ew-resize"
        style={{ left: `${position}%`, top: '50%', transform: 'translate(-50%, -50%)' }}
      >
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 border-[3px] border-white shadow-xl shadow-primary-500/40 flex items-center justify-center">
          <div className="flex items-center gap-0.5">
            <FiChevronLeft className="w-3 h-3 text-white" />
            <FiChevronRight className="w-3 h-3 text-white" />
          </div>
        </div>
      </div>

      {/* Labels */}
      <div className="absolute top-3 left-3 z-10">
        <span className="px-2.5 py-1 rounded-lg bg-surface-900/80 backdrop-blur-sm text-xs font-medium text-surface-200 border border-surface-700/50">
          {beforeLabel}
        </span>
      </div>
      <div className="absolute top-3 right-3 z-10">
        <span className="px-2.5 py-1 rounded-lg bg-surface-900/80 backdrop-blur-sm text-xs font-medium text-surface-200 border border-surface-700/50">
          {afterLabel}
        </span>
      </div>
    </div>
  );
}
