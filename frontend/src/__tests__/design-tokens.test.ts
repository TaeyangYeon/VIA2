import { colors, typography, spacing, transitions } from '../styles/design-tokens';

describe('Design Tokens — colors', () => {
  const requiredBackgrounds = ['top', 'card', 'secondary', 'hover'];
  const requiredBorders = ['default', 'accent'];
  const requiredText = ['primary', 'secondary', 'disabled'];
  const requiredAccent = ['action', 'success', 'warning', 'error', 'info'];

  const hexRe = /^#[0-9a-fA-F]{3}([0-9a-fA-F]{3})?$/;

  it('has all background keys', () => {
    requiredBackgrounds.forEach((k) => {
      expect(colors.background).toHaveProperty(k);
    });
  });

  it('has all border keys', () => {
    requiredBorders.forEach((k) => {
      expect(colors.border).toHaveProperty(k);
    });
  });

  it('has all text keys', () => {
    requiredText.forEach((k) => {
      expect(colors.text).toHaveProperty(k);
    });
  });

  it('has all accent keys', () => {
    requiredAccent.forEach((k) => {
      expect(colors.accent).toHaveProperty(k);
    });
  });

  it('all color values are valid hex strings', () => {
    const allValues = [
      ...Object.values(colors.background),
      ...Object.values(colors.border),
      ...Object.values(colors.text),
      ...Object.values(colors.accent),
    ];
    allValues.forEach((v) => {
      expect(v).toMatch(hexRe);
    });
  });

  it('background colors are dark neutrals (not blue/purple)', () => {
    const darkBgs = ['#0a0a0a', '#111111', '#1a1a1a', '#222222'];
    Object.values(colors.background).forEach((v) => {
      expect(darkBgs).toContain(v);
    });
  });
});

describe('Design Tokens — typography', () => {
  it('has fontFamily with body and code', () => {
    expect(typography.fontFamily).toHaveProperty('body');
    expect(typography.fontFamily).toHaveProperty('code');
  });

  it('body font stack includes Inter', () => {
    expect(typography.fontFamily.body).toContain('Inter');
  });

  it('code font stack includes JetBrains Mono', () => {
    expect(typography.fontFamily.code).toContain('JetBrains Mono');
  });
});

describe('Design Tokens — spacing', () => {
  it('has a base unit of 8', () => {
    expect(spacing.base).toBe(8);
  });
});

describe('Design Tokens — transitions', () => {
  it('has a default transition string', () => {
    expect(typeof transitions.default).toBe('string');
    expect(transitions.default.length).toBeGreaterThan(0);
  });
});
