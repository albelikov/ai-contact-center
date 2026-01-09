/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'ua-blue': '#0057B8',
        'ua-gold': '#FFD700',
      }
    },
  },
  plugins: [],
}
