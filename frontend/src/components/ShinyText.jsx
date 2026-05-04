/*
 * ShinyText.jsx — React Bits ShinyText (pure CSS version, no framer-motion dep)
 */
const ShinyText = ({
  text,
  className = '',
  color = '#94a3b8',
  shineColor = '#ffffff',
  speed = 3,
  disabled = false,
}) => {
  const style = disabled
    ? { color }
    : {
        backgroundImage: `linear-gradient(
          120deg,
          ${color} 0%,
          ${color} 30%,
          ${shineColor} 50%,
          ${color} 70%,
          ${color} 100%
        )`,
        backgroundSize: '250% auto',
        WebkitBackgroundClip: 'text',
        backgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        animation: `shiny-text-sweep ${speed}s linear infinite`,
      };

  return (
    <span className={`shiny-text-wrap ${className}`} style={style}>
      {text}
    </span>
  );
};

export default ShinyText;
