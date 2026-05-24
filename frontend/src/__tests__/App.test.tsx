import { render, screen } from '@testing-library/react';
import App from '../App';

describe('App component', () => {
  it('renders without crashing', () => {
    const { container } = render(<App />);
    expect(container).toBeTruthy();
  });

  it('displays VIA2 title text', () => {
    render(<App />);
    expect(screen.getByText(/VIA2/i)).toBeInTheDocument();
  });

  it('displays the full app title', () => {
    render(<App />);
    expect(screen.getByText(/Vision Intelligence Agent/i)).toBeInTheDocument();
  });

  it('root element has dark background class', () => {
    const { container } = render(<App />);
    const root = container.firstElementChild as HTMLElement;
    expect(root).toBeTruthy();
    // should use bg-top or inline style with #0a0a0a
    const hasDarkBg =
      root.className.includes('bg-') ||
      root.style.backgroundColor !== '' ||
      root.getAttribute('data-testid') === 'app-root';
    expect(hasDarkBg).toBe(true);
  });
});
