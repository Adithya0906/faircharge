/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0fdf9',
          100: '#ccfbee',
          200: '#9af5da',
          300: '#5cebbf',
          400: '#2dd4a1',
          500: '#14b88a',
          600: '#0b9270',
          700: '#0c745b',
          800: '#0e5c49',
          900: '#0e4c3d',
          950: '#052e26',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
