/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50:'#eef7ff',100:'#d9ecff',200:'#bbdeff',300:'#8ccaff',
          400:'#55adff',500:'#2d8bff',600:'#1a6df5',700:'#1356e1',
          800:'#1646b6',900:'#183e8f',950:'#132757',
        },
        accent: {
          50:'#effefb',100:'#c7fff4',200:'#90ffe9',300:'#51f7da',
          400:'#1de4c6',500:'#05c8ad',600:'#00a18e',700:'#058073',
          800:'#0a655d',900:'#0d534d',950:'#003331',
        },
        surface: {
          50:'#f8fafc',100:'#f1f5f9',200:'#e2e8f0',300:'#cbd5e1',
          400:'#94a3b8',500:'#64748b',600:'#475569',700:'#334155',
          800:'#1e293b',850:'#172032',900:'#0f172a',950:'#020617',
        },
      },
      fontFamily: {
        sans: ['Space Grotesk','Inter','system-ui','-apple-system','sans-serif'],
        mono: ['JetBrains Mono','monospace'],
        display: ['Orbitron','Space Grotesk','sans-serif'],
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'float':      'float 6s ease-in-out infinite',
        'slide-up':   'slide-up 0.55s cubic-bezier(0.4,0,0.2,1) both',
        'slide-in':   'slide-in 0.3s ease-out',
        'scale-in':   'scale-in 0.3s ease-out both',
        'shimmer':    'shimmer 2s linear infinite',
        'fade-in':    'fade-in 0.4s ease-out both',
        'spin-slow':  'spin 3s linear infinite',
      },
      keyframes: {
        'pulse-glow': {
          '0%,100%': { boxShadow:'0 0 20px rgba(124,58,237,0.3)' },
          '50%':     { boxShadow:'0 0 40px rgba(124,58,237,0.7)' },
        },
        'float': {
          '0%,100%': { transform:'translateY(0px)' },
          '50%':     { transform:'translateY(-10px)' },
        },
        'slide-up': {
          '0%':   { opacity:'0', transform:'translateY(24px)' },
          '100%': { opacity:'1', transform:'translateY(0)' },
        },
        'slide-in': {
          '0%':   { opacity:'0', transform:'translateX(-10px)' },
          '100%': { opacity:'1', transform:'translateX(0)' },
        },
        'scale-in': {
          '0%':   { opacity:'0', transform:'scale(0.94)' },
          '100%': { opacity:'1', transform:'scale(1)' },
        },
        'shimmer': {
          '0%':   { backgroundPosition:'-200% 0' },
          '100%': { backgroundPosition:'200% 0' },
        },
        'fade-in': {
          '0%':   { opacity:'0' },
          '100%': { opacity:'1' },
        },
      },
      backdropBlur: { xs:'2px' },
    },
  },
  plugins: [],
}
