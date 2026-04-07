/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        soc: {
          950: '#05070d',
          900: '#0b1220',
          800: '#101a2e',
          700: '#1b2a46',
          600: '#2a3f66',
          accent: '#1ecad3',
          danger: '#ef4444',
          warning: '#f59e0b',
          success: '#10b981',
        },
      },
      boxShadow: {
        panel: '0 10px 30px rgba(5, 8, 18, 0.45)',
      },
      fontFamily: {
        display: ['Rajdhani', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

