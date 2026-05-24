export const colors = {
  background: {
    top: '#0a0a0a',
    card: '#111111',
    secondary: '#1a1a1a',
    hover: '#222222',
  },
  border: {
    default: '#2a2a2a',
    accent: '#3a3a3a',
  },
  text: {
    primary: '#f5f5f5',
    secondary: '#a0a0a0',
    disabled: '#555555',
  },
  accent: {
    action: '#ffffff',
    success: '#4ade80',
    warning: '#facc15',
    error: '#f87171',
    info: '#60a5fa',
  },
};

export const typography = {
  fontFamily: {
    body: 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    code: '"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
  },
  fontSize: {
    xs: '0.75rem',
    sm: '0.875rem',
    base: '1rem',
    lg: '1.125rem',
    xl: '1.25rem',
    '2xl': '1.5rem',
  },
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
};

export const spacing = {
  base: 8,
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  '2xl': '48px',
  '3xl': '64px',
};

export const transitions = {
  default: 'all 150ms ease-in-out',
  fast: 'all 75ms ease-in-out',
  slow: 'all 300ms ease-in-out',
};

export const glassMorphism = {
  panel: {
    background: 'rgba(17, 17, 17, 0.85)',
    backdropFilter: 'blur(12px)',
    border: '1px solid #2a2a2a',
  },
  card: {
    background: 'rgba(26, 26, 26, 0.80)',
    backdropFilter: 'blur(8px)',
    border: '1px solid #2a2a2a',
  },
};
