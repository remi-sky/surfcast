/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
      './index.html',
      './src/**/*.{js,jsx,ts,tsx}',
    ],
    safelist: [
      'bg-gradient-to-r',
      'from-gradient-start',
      'to-gradient-end',
    ],
    theme: {
      extend: {
        colors: {
          'gradient-start': 'var(--gradient-start)',
          'gradient-end':   'var(--gradient-end)',
          'gradient-middle': 'var(--gradient-middle)',
          'accent-teal':    'var(--accent-teal)',
        },
        backdropBlur: {
          lg: '20px',
        },
      },
    },
    plugins: [],
  };
  