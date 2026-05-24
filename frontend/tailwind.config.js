/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'bg-top': '#0a0a0a',
        'bg-card': '#111111',
        'bg-secondary': '#1a1a1a',
        'bg-hover': '#222222',
        'border-default': '#2a2a2a',
        'border-accent': '#3a3a3a',
        'text-primary': '#f5f5f5',
        'text-secondary': '#a0a0a0',
        'text-disabled': '#555555',
        'accent-action': '#ffffff',
        'accent-success': '#4ade80',
        'accent-warning': '#facc15',
        'accent-error': '#f87171',
        'accent-info': '#60a5fa',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
      spacing: {
        'grid': '8px',
      },
      backdropBlur: {
        xs: '2px',
      },
      transitionDuration: {
        DEFAULT: '150ms',
      },
    },
  },
  plugins: [],
};
