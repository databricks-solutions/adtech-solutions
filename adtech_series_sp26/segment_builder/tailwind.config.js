/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./frontend/index.html",
    "./frontend/src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        databricks: {
          orange: '#FF3621',
          dark: '#1B3139',
        },
      },
    },
  },
  plugins: [],
}
