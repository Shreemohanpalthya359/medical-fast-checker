export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans:    ['Inter', 'system-ui', 'sans-serif'],
        display: ['Syne', 'sans-serif'],
      },
      colors: {
        surface: {
          1: 'rgb(2 8 23)',
          2: 'rgb(7 15 35)',
          3: 'rgb(10 22 50)',
        },
        medical: {
          50:  '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#14b8a6',
          600: '#0d9488',
          700: '#0f766e',
          800: '#115e59',
          900: '#134e4a',
        }
      },
      backgroundImage: {
        'grid-pattern': "linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)",
      },
      backgroundSize: {
        'grid': '40px 40px',
      },
      animation: {
        'spin-slow': 'spin 8s linear infinite',
        'float':     'float 6s ease-in-out infinite',
        'shimmer':   'shimmer 2s infinite linear',
        'fade-up':   'fade-up 0.5s ease-out forwards',
      },
      keyframes: {
        float:   { '0%,100%': { transform: 'translateY(0px)' }, '50%': { transform: 'translateY(-12px)' } },
        shimmer: { '0%': { backgroundPosition: '-1000px 0' }, '100%': { backgroundPosition: '1000px 0' } },
        'fade-up': { from: { opacity: '0', transform: 'translateY(16px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
      },
      boxShadow: {
        'glow-teal':  '0 0 30px rgba(20,184,166,0.25)',
        'glow-blue':  '0 0 30px rgba(99,102,241,0.25)',
        'glow-rose':  '0 0 30px rgba(244,63,94,0.25)',
        'inner-top':  'inset 0 1px 0 rgba(255,255,255,0.06)',
      }
    },
  },
  plugins: [],
}
