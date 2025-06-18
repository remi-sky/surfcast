/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
      './index.html',
      './src/**/*.{js,jsx,ts,tsx}',
    ],
    theme: {
      extend: {
        colors: {
          'gradient-start': 'var(--gradient-start)',
          'gradient-end':   'var(--gradient-end)',
          'accent-teal':    'var(--accent-teal)',
        },
        backdropBlur: {
          // ensure blur-lg is available
          lg: '20px',
        }
      },
    },
    plugins: [],
  };
  