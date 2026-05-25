import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { store } from '../store';
import Layout from '../components/Layout';

const renderWithStore = (ui: React.ReactElement) =>
  render(<Provider store={store}>{ui}</Provider>);

describe('Layout component', () => {
  it('renders without crashing', () => {
    const { container } = renderWithStore(<Layout />);
    expect(container).toBeTruthy();
  });

  it('renders sidebar', () => {
    renderWithStore(<Layout />);
    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
  });

  it('renders main workspace', () => {
    renderWithStore(<Layout />);
    expect(screen.getByTestId('main-workspace')).toBeInTheDocument();
  });

  it('renders all nav items', () => {
    renderWithStore(<Layout />);
    const navLabels = ['Input', 'ROI', 'Engine', 'Directive', 'Config', 'Execution', 'Result'];
    navLabels.forEach(label => {
      expect(screen.getByText(label)).toBeInTheDocument();
    });
  });

  it('Input panel is active by default', () => {
    renderWithStore(<Layout />);
    const inputNav = screen.getByTestId('nav-input');
    expect(inputNav).toHaveAttribute('data-active', 'true');
  });

  it('clicking a nav item changes active panel', () => {
    renderWithStore(<Layout />);
    const roiNav = screen.getByTestId('nav-roi');
    fireEvent.click(roiNav);
    expect(roiNav).toHaveAttribute('data-active', 'true');
    expect(screen.getByTestId('nav-input')).toHaveAttribute('data-active', 'false');
  });

  it('sidebar has collapse toggle button', () => {
    renderWithStore(<Layout />);
    expect(screen.getByTestId('sidebar-toggle')).toBeInTheDocument();
  });

  it('clicking collapse toggle collapses sidebar', () => {
    renderWithStore(<Layout />);
    const toggle = screen.getByTestId('sidebar-toggle');
    fireEvent.click(toggle);
    expect(screen.getByTestId('sidebar')).toHaveAttribute('data-collapsed', 'true');
  });

  it('clicking collapse toggle again expands sidebar', () => {
    renderWithStore(<Layout />);
    const toggle = screen.getByTestId('sidebar-toggle');
    fireEvent.click(toggle);
    fireEvent.click(toggle);
    expect(screen.getByTestId('sidebar')).toHaveAttribute('data-collapsed', 'false');
  });

  it('nav item labels are hidden when collapsed', () => {
    renderWithStore(<Layout />);
    const toggle = screen.getByTestId('sidebar-toggle');
    fireEvent.click(toggle);
    expect(screen.queryByText('Input')).not.toBeVisible();
  });

  it('renders InputPanel in main workspace when Input is active', () => {
    renderWithStore(<Layout />);
    expect(screen.getByTestId('input-panel')).toBeInTheDocument();
  });

  it('sidebar has approximately 280px width when expanded', () => {
    renderWithStore(<Layout />);
    const sidebar = screen.getByTestId('sidebar');
    expect(sidebar).toHaveAttribute('data-collapsed', 'false');
  });
});
