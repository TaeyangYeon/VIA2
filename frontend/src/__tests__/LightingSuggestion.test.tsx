import { render, screen, fireEvent } from '@testing-library/react';
import LightingSuggestion from '../components/LightingSuggestion';

const mockSuggestions = [
  'Use ring light at 45-degree angle for uniform illumination',
  'Consider adding backlight to enhance edge contrast',
  'High-angle coaxial light recommended for flat surface inspection',
];

describe('LightingSuggestion', () => {
  beforeEach(() => {
    jest.spyOn(window, 'open').mockImplementation(() => null);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders without crashing', () => {
    const { container } = render(<LightingSuggestion suggestions={mockSuggestions} />);
    expect(container).toBeTruthy();
  });

  it('has data-testid="lighting-suggestion-list"', () => {
    render(<LightingSuggestion suggestions={mockSuggestions} />);
    expect(screen.getByTestId('lighting-suggestion-list')).toBeInTheDocument();
  });

  it('renders all suggestion cards', () => {
    render(<LightingSuggestion suggestions={mockSuggestions} />);
    expect(screen.getByTestId('lighting-card-0')).toBeInTheDocument();
    expect(screen.getByTestId('lighting-card-1')).toBeInTheDocument();
    expect(screen.getByTestId('lighting-card-2')).toBeInTheDocument();
  });

  it('renders suggestion text content', () => {
    render(<LightingSuggestion suggestions={mockSuggestions} />);
    expect(
      screen.getByText('Use ring light at 45-degree angle for uniform illumination')
    ).toBeInTheDocument();
    expect(
      screen.getByText('Consider adding backlight to enhance edge contrast')
    ).toBeInTheDocument();
  });

  it('renders all suggestions text', () => {
    render(<LightingSuggestion suggestions={mockSuggestions} />);
    mockSuggestions.forEach(s => {
      expect(screen.getByText(s)).toBeInTheDocument();
    });
  });

  it('has open-light-test-btn', () => {
    render(<LightingSuggestion suggestions={mockSuggestions} />);
    expect(screen.getByTestId('open-light-test-btn')).toBeInTheDocument();
  });

  it('calls window.open with "#/light-test" when Open Light Test is clicked (no Electron)', () => {
    render(<LightingSuggestion suggestions={mockSuggestions} />);
    fireEvent.click(screen.getByTestId('open-light-test-btn'));
    expect(window.open).toHaveBeenCalledWith('#/light-test', '_blank');
  });

  it('calls electronAPI.openLightTest when available', () => {
    const mockOpenLightTest = jest.fn();
    Object.defineProperty(window, 'electronAPI', {
      value: { openLightTest: mockOpenLightTest },
      writable: true,
      configurable: true,
    });
    render(<LightingSuggestion suggestions={mockSuggestions} />);
    fireEvent.click(screen.getByTestId('open-light-test-btn'));
    expect(mockOpenLightTest).toHaveBeenCalled();
    expect(window.open).not.toHaveBeenCalled();
    delete (window as unknown as { electronAPI?: unknown }).electronAPI;
  });

  it('renders with empty suggestions array without crashing', () => {
    const { container } = render(<LightingSuggestion suggestions={[]} />);
    expect(container).toBeTruthy();
  });

  it('shows no lighting cards when suggestions is empty', () => {
    render(<LightingSuggestion suggestions={[]} />);
    expect(screen.queryByTestId('lighting-card-0')).not.toBeInTheDocument();
  });
});
