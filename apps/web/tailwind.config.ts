import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        bg:     'var(--bg)',
        panel:  'var(--panel)',
        line:   'var(--line)',
        'text-primary': 'var(--text)',
        muted:  'var(--muted)',
        accent: 'var(--accent)',
        up:     'var(--up)',
        down:   'var(--down)',
        warn:   'var(--warn)',
        input:  'var(--input)',
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', '"Segoe UI"', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', '"SF Mono"', 'ui-monospace', 'monospace'],
      },
      borderColor: {
        DEFAULT: 'var(--line)',
      },
    },
  },
  plugins: [],
};

export default config;
