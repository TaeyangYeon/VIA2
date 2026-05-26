import { render, screen } from '@testing-library/react';
import MetricsChart from '../components/MetricsChart';

const mockItemResults = [
  { item_id: 'item-1', category: 'defect_detection', passed: true,  accuracy: 0.95, fp_rate: 0.02, fn_rate: 0.03 },
  { item_id: 'item-2', category: 'surface_check',    passed: false, accuracy: 0.72, fp_rate: 0.15, fn_rate: 0.13 },
  { item_id: 'item-3', category: 'size_measurement', passed: true,  accuracy: 0.98, fp_rate: 0.01, fn_rate: 0.01 },
];

describe('MetricsChart', () => {
  it('renders without crashing', () => {
    const { container } = render(<MetricsChart itemResults={mockItemResults} />);
    expect(container).toBeTruthy();
  });

  it('has data-testid="metrics-table"', () => {
    render(<MetricsChart itemResults={mockItemResults} />);
    expect(screen.getByTestId('metrics-table')).toBeInTheDocument();
  });

  it('renders all item IDs', () => {
    render(<MetricsChart itemResults={mockItemResults} />);
    expect(screen.getByText('item-1')).toBeInTheDocument();
    expect(screen.getByText('item-2')).toBeInTheDocument();
    expect(screen.getByText('item-3')).toBeInTheDocument();
  });

  it('renders category for each item', () => {
    render(<MetricsChart itemResults={mockItemResults} />);
    expect(screen.getByText('defect_detection')).toBeInTheDocument();
    expect(screen.getByText('surface_check')).toBeInTheDocument();
    expect(screen.getByText('size_measurement')).toBeInTheDocument();
  });

  it('shows pass status for passed items', () => {
    render(<MetricsChart itemResults={mockItemResults} />);
    expect(screen.getByTestId('status-passed-item-1')).toBeInTheDocument();
    expect(screen.getByTestId('status-passed-item-3')).toBeInTheDocument();
  });

  it('shows fail status for failed items', () => {
    render(<MetricsChart itemResults={mockItemResults} />);
    expect(screen.getByTestId('status-failed-item-2')).toBeInTheDocument();
  });

  it('shows FP rate bar for each item', () => {
    render(<MetricsChart itemResults={mockItemResults} />);
    expect(screen.getByTestId('fp-bar-item-1')).toBeInTheDocument();
    expect(screen.getByTestId('fp-bar-item-2')).toBeInTheDocument();
    expect(screen.getByTestId('fp-bar-item-3')).toBeInTheDocument();
  });

  it('shows FN rate bar for each item', () => {
    render(<MetricsChart itemResults={mockItemResults} />);
    expect(screen.getByTestId('fn-bar-item-1')).toBeInTheDocument();
    expect(screen.getByTestId('fn-bar-item-2')).toBeInTheDocument();
    expect(screen.getByTestId('fn-bar-item-3')).toBeInTheDocument();
  });

  it('shows metrics-summary-row', () => {
    render(<MetricsChart itemResults={mockItemResults} />);
    expect(screen.getByTestId('metrics-summary-row')).toBeInTheDocument();
  });

  it('shows correct pass count in summary row', () => {
    render(<MetricsChart itemResults={mockItemResults} />);
    const row = screen.getByTestId('metrics-summary-row');
    expect(row.textContent).toContain('2 pass');
  });

  it('shows correct fail count in summary row', () => {
    render(<MetricsChart itemResults={mockItemResults} />);
    const row = screen.getByTestId('metrics-summary-row');
    expect(row.textContent).toContain('1 fail');
  });

  it('fp-bar-item-1 has width 2%', () => {
    render(<MetricsChart itemResults={mockItemResults} />);
    const bar = screen.getByTestId('fp-bar-item-1');
    expect(bar.style.width).toBe('2%');
  });

  it('renders with empty results array', () => {
    const { container } = render(<MetricsChart itemResults={[]} />);
    expect(container).toBeTruthy();
  });

  it('shows 0 pass 0 fail in summary when results is empty', () => {
    render(<MetricsChart itemResults={[]} />);
    const row = screen.getByTestId('metrics-summary-row');
    expect(row.textContent).toContain('0 pass');
    expect(row.textContent).toContain('0 fail');
  });
});
