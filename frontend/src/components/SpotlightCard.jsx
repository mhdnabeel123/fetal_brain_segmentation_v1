/*
 * SpotlightCard.jsx — React Bits Spotlight Card (mouse-tracking radial glow)
 * No external dependencies required
 */
import { useRef } from 'react';

const SpotlightCard = ({
  children,
  className = '',
  spotlightColor = 'rgba(124, 58, 237, 0.18)',
  style = {},
}) => {
  const ref = useRef(null);

  const handleMouseMove = (e) => {
    if (!ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    ref.current.style.setProperty('--mouse-x', `${e.clientX - rect.left}px`);
    ref.current.style.setProperty('--mouse-y', `${e.clientY - rect.top}px`);
    ref.current.style.setProperty('--spotlight-color', spotlightColor);
  };

  return (
    <div
      ref={ref}
      onMouseMove={handleMouseMove}
      className={`spotlight-card ${className}`}
      style={style}
    >
      {children}
    </div>
  );
};

export default SpotlightCard;
