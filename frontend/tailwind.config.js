/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
        },
        surface: {
          950: '#0a0f1a',
          900: '#111827',
          800: '#1e293b',
          700: '#334155',
        },
      },
    },
  },
  plugins: [],
};
