import { render, screen } from '@testing-library/react';
import App from '../App';

describe('App component', () => {
  it('renders without crashing', () => {
    const { container } = render(<App />);
    expect(container).toBeTruthy();
  });

  it('renders the layout', () => {
    render(<App />);
    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
    expect(screen.getByTestId('main-workspace')).toBeInTheDocument();
  });

  it('root element has app-root testid', () => {
    render(<App />);
    expect(screen.getByTestId('app-root')).toBeInTheDocument();
  });

  it('renders VIA2 brand in sidebar', () => {
    render(<App />);
    expect(screen.getByText(/VIA2/i)).toBeInTheDocument();
  });
});
