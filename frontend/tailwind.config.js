/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // Enable class-based dark mode
  theme: {
    extend: {
      colors: {
        background: {
          light: '#f8fafc',
          dark: '#06090f',
        },
        surface: {
          light: '#ffffff',
          dark: '#090e1b',
        },
        card: {
          light: '#f1f5f9',
          dark: '#0d1424',
        },
        cardHover: {
          light: '#e2e8f0',
          dark: '#111b30',
        },
        borderBase: {
          light: 'rgba(59,130,246,0.15)',
          dark: 'rgba(59,130,246,0.12)',
        },
        textMain: {
          light: '#0f172a',
          dark: '#f8fafc',
        },
        textMuted: {
          light: '#64748b',
          dark: '#8b9bb4',
        },
        primary: {
          DEFAULT: '#3b82f6',
          hover: '#2563eb',
        },
        accent: {
          DEFAULT: '#60a5fa',
        },
        alert: '#ef4444',
        success: '#10b981',
        warning: '#f59e0b',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['"Exo 2"', 'sans-serif'], // For headings/logos
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'orbit': 'orbit 20s linear infinite',
      },
      keyframes: {
        orbit: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        }
      }
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
