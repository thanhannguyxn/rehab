/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class', // Enable class-based dark mode
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontSize: {
        'xs':   ['13px', { lineHeight: '1.5' }],
        'sm':   ['15px', { lineHeight: '1.5' }],
        'base': ['17px', { lineHeight: '1.6' }],
        'lg':   ['20px', { lineHeight: '1.6' }],
        'xl':   ['23px', { lineHeight: '1.4' }],
        '2xl':  ['27px', { lineHeight: '1.3' }],
        '3xl':  ['33px', { lineHeight: '1.25' }],
        '4xl':  ['40px', { lineHeight: '1.2' }],
        '5xl':  ['48px', { lineHeight: '1.15' }],
        '6xl':  ['58px', { lineHeight: '1.1' }],
      },
      spacing: {
        '18': '4.5rem',
        '72': '18rem',
        '84': '21rem',
        '96': '24rem',
      }
    },
  },
  plugins: [],
}
