/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // FIAP Brand Colors
        fiap: {
          pink: '#ED145B',
          'pink-light': '#F05A85',
          'pink-dark': '#C4124D',
          black: '#1A1A1A',
          'gray-900': '#0f172a',
          'gray-800': '#1e293b',
          'gray-700': '#334155',
          'gray-600': '#475569',
          'gray-500': '#64748b',
          'gray-400': '#94a3b8',
          white: '#FFFFFF',
        },
        // Keep slate for compatibility
        slate: {
          850: '#1e293b',
          900: '#0f172a',
          950: '#020617',
        },
      },
      fontFamily: {
        fiap: ['Montserrat', 'Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
