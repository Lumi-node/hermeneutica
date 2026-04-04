import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: '#0a0a0f',
          secondary: '#12121a',
          panel: '#1a1a2e',
        },
        accent: {
          blue: '#4A90D9',
          gold: '#E8A838',
          green: '#50C878',
          purple: '#7B68EE',
          red: '#FF6B6B',
          pink: '#DDA0DD',
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
