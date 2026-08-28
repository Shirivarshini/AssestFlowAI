/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['HelveticaNowDisplay', 'Neue Haas Grotesk Display', 'Helvetica Neue', 'Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

