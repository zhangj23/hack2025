/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'retro': {
          'brown': '#8B4513',
          'tan': '#D2B48C',
          'cream': '#F5E6D3',
        },
        'modern': {
          'blue': '#3B82F6',
          'cyan': '#06B6D4',
          'teal': '#14B8A6',
        }
      },
      fontFamily: {
        'handwriting': ['Kalam', 'cursive'],
      }
    },
  },
  plugins: [],
}

