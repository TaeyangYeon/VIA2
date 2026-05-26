import { render, screen, fireEvent } from '@testing-library/react';
import ParameterSheet from '../components/ParameterSheet';

const mockData = {
  'node-1': {
    threshold: 0.5,
    iterations: 10,
    method: 'gradient_descent',
  },
  'node-2': {
    kernel_size: 3,
    sigma: 1.5,
  },
};

describe('ParameterSheet', () => {
  it('renders without crashing', () => {
    const { container } = render(
      <ParameterSheet isOpen={true} nodeId={null} data={null} onClose={jest.fn()} />
    );
    expect(container).toBeTruthy();
  });

  it('has data-testid="parameter-sheet"', () => {
    render(<ParameterSheet isOpen={true} nodeId={null} data={null} onClose={jest.fn()} />);
    expect(screen.getByTestId('parameter-sheet')).toBeInTheDocument();
  });

  it('has display flex when isOpen is true', () => {
    render(<ParameterSheet isOpen={true} nodeId="node-1" data={mockData} onClose={jest.fn()} />);
    const sheet = screen.getByTestId('parameter-sheet');
    expect(sheet.style.display).toBe('flex');
  });

  it('has display none when isOpen is false', () => {
    render(<ParameterSheet isOpen={false} nodeId="node-1" data={mockData} onClose={jest.fn()} />);
    const sheet = screen.getByTestId('parameter-sheet');
    expect(sheet.style.display).toBe('none');
  });

  it('shows the nodeId in parameter-node-id', () => {
    render(<ParameterSheet isOpen={true} nodeId="node-1" data={mockData} onClose={jest.fn()} />);
    expect(screen.getByTestId('parameter-node-id').textContent).toBe('node-1');
  });

  it('shows all parameter keys for the selected node', () => {
    render(<ParameterSheet isOpen={true} nodeId="node-1" data={mockData} onClose={jest.fn()} />);
    expect(screen.getByText('threshold')).toBeInTheDocument();
    expect(screen.getByText('iterations')).toBeInTheDocument();
    expect(screen.getByText('method')).toBeInTheDocument();
  });

  it('shows correct parameter values for selected node', () => {
    render(<ParameterSheet isOpen={true} nodeId="node-1" data={mockData} onClose={jest.fn()} />);
    expect(screen.getByTestId('param-value-threshold').textContent).toBe('0.5');
    expect(screen.getByTestId('param-value-iterations').textContent).toBe('10');
    expect(screen.getByTestId('param-value-method').textContent).toBe('gradient_descent');
  });

  it('shows parameters for node-2 when nodeId is node-2', () => {
    render(<ParameterSheet isOpen={true} nodeId="node-2" data={mockData} onClose={jest.fn()} />);
    expect(screen.getByText('kernel_size')).toBeInTheDocument();
    expect(screen.getByText('sigma')).toBeInTheDocument();
  });

  it('shows empty message when nodeId has no matching data', () => {
    render(<ParameterSheet isOpen={true} nodeId="node-999" data={mockData} onClose={jest.fn()} />);
    expect(screen.getByText(/no parameters available/i)).toBeInTheDocument();
  });

  it('shows empty message when data is null', () => {
    render(<ParameterSheet isOpen={true} nodeId="node-1" data={null} onClose={jest.fn()} />);
    expect(screen.getByText(/no parameters available/i)).toBeInTheDocument();
  });

  it('shows empty message when nodeId is null', () => {
    render(<ParameterSheet isOpen={true} nodeId={null} data={mockData} onClose={jest.fn()} />);
    expect(screen.getByText(/no parameters available/i)).toBeInTheDocument();
  });

  it('calls onClose when parameter-close-btn is clicked', () => {
    const onClose = jest.fn();
    render(<ParameterSheet isOpen={true} nodeId="node-1" data={mockData} onClose={onClose} />);
    fireEvent.click(screen.getByTestId('parameter-close-btn'));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
