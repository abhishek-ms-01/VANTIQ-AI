/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'sans-serif'],
      },
      colors: {
        dark: {
          bg: '#0f1115',
          card: '#161920',
          border: '#2a2e39',
          text: '#e2e8f0',
          muted: '#94a3b8'
        },
        light: {
          bg: '#f8fafc',
          card: '#ffffff',
          border: '#e2e8f0',
          text: '#0f172a',
          muted: '#64748b'
        },
        market: {
          up: '#10b981',
          down: '#ef4444',
          warn: '#f59e0b'
        }
      },
    },
  },
  plugins: [],
}
