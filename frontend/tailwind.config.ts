/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
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
        success: {
          50: '#f0fdf4',
          500: '#22c55e',
          800: '#166534',
        },
        warning: {
          50: '#fffbeb',
          500: '#d97706',
          800: '#78350f',
        },
        danger: {
          50: '#fef2f2',
          500: '#ef4444',
          800: '#991b1b',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      maxWidth: {
        'screen-xl': '1320px',
      },
    },
  },
  plugins: [],
  darkMode: 'class',
}
