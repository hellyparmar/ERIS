/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Brand base
        brand: {
          50: '#f4f5ff',
          100: '#eaecff',
          200: '#d8dcff',
          300: '#b1b8ff',
          400: '#818cff',
          500: '#5e68ff',
          600: '#4b55e3',
          700: '#3d45b3',
          800: '#343b89',
          900: '#2d336f',
        },
        // Semantic
        success: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
        warning: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#f59e0b',
          500: '#d97706',
          600: '#b45309',
          700: '#92400e',
          800: '#78350f',
          900: '#5f370e',
        },
        danger: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d',
        },
        // UI neutrals for modern soft mode and dark mode
        surface: {
          50: '#f8f8f9',
          100: '#f0f2f7',
          200: '#e2e7f0',
          300: '#d4dbe6',
          400: '#bfc8d8',
          500: '#a8b3c9',
          600: '#7f8aa0',
          700: '#5f6781',
          800: '#434f63',
          900: '#2d3950',
        },
      },
      boxShadow: {
        'soft': '0 8px 24px rgba(15, 23, 42, 0.08)',
        'soft-dark': '0 8px 24px rgba(7, 10, 18, 0.65)',
        'glow': '0 0 14px rgba(110, 103, 255, 0.45)',
      },
      borderRadius: {
        'xl': '1.1rem',
        '2xl': '1.8rem',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      gridTemplateColumns: {
        'dashboard': 'repeat(12, minmax(0, 1fr))',
      },
      maxWidth: {
        'screen-xl': '1320px',
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
  darkMode: 'class',
}
