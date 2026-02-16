/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'trading-dark': '#0f172a',
        'trading-card': '#1e293b',
      }
    },
  },
  plugins: [],
}
