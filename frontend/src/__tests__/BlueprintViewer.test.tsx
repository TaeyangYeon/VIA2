import { render, screen, fireEvent } from '@testing-library/react';
import BlueprintViewer from '../components/BlueprintViewer';

const mockSvg =
  '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">' +
  '<rect data-node-id="node-1" x="10" y="10" width="80" height="80" />' +
  '<circle data-node-id="node-2" cx="150" cy="50" r="30" />' +
  '</svg>';

describe('BlueprintViewer', () => {
  it('renders without crashing', () => {
    const { container } = render(<BlueprintViewer svgContent={mockSvg} />);
    expect(container).toBeTruthy();
  });

  it('has data-testid="blueprint-viewer"', () => {
    render(<BlueprintViewer svgContent={mockSvg} />);
    expect(screen.getByTestId('blueprint-viewer')).toBeInTheDocument();
  });

  it('renders SVG content into the DOM', () => {
    const { container } = render(<BlueprintViewer svgContent={mockSvg} />);
    expect(container.querySelector('svg')).toBeInTheDocument();
  });

  it('has zoom-in-btn', () => {
    render(<BlueprintViewer svgContent={mockSvg} />);
    expect(screen.getByTestId('zoom-in-btn')).toBeInTheDocument();
  });

  it('has zoom-out-btn', () => {
    render(<BlueprintViewer svgContent={mockSvg} />);
    expect(screen.getByTestId('zoom-out-btn')).toBeInTheDocument();
  });

  it('has reset-btn', () => {
    render(<BlueprintViewer svgContent={mockSvg} />);
    expect(screen.getByTestId('reset-btn')).toBeInTheDocument();
  });

  it('has fit-btn', () => {
    render(<BlueprintViewer svgContent={mockSvg} />);
    expect(screen.getByTestId('fit-btn')).toBeInTheDocument();
  });

  it('shows 100% scale initially in scale-display', () => {
    render(<BlueprintViewer svgContent={mockSvg} />);
    expect(screen.getByTestId('scale-display').textContent).toBe('100%');
  });

  it('clicking zoom-in increases scale to 125%', () => {
    render(<BlueprintViewer svgContent={mockSvg} />);
    fireEvent.click(screen.getByTestId('zoom-in-btn'));
    expect(screen.getByTestId('scale-display').textContent).toBe('125%');
  });

  it('clicking zoom-out decreases scale to 75%', () => {
    render(<BlueprintViewer svgContent={mockSvg} />);
    fireEvent.click(screen.getByTestId('zoom-out-btn'));
    expect(screen.getByTestId('scale-display').textContent).toBe('75%');
  });

  it('clicking reset-btn resets scale to 100% after zooming in', () => {
    render(<BlueprintViewer svgContent={mockSvg} />);
    fireEvent.click(screen.getByTestId('zoom-in-btn'));
    fireEvent.click(screen.getByTestId('zoom-in-btn'));
    fireEvent.click(screen.getByTestId('reset-btn'));
    expect(screen.getByTestId('scale-display').textContent).toBe('100%');
  });

  it('does not zoom below 25% (min clamp)', () => {
    render(<BlueprintViewer svgContent={mockSvg} />);
    for (let i = 0; i < 20; i++) {
      fireEvent.click(screen.getByTestId('zoom-out-btn'));
    }
    expect(screen.getByTestId('scale-display').textContent).toBe('25%');
  });

  it('does not zoom above 400% (max clamp)', () => {
    render(<BlueprintViewer svgContent={mockSvg} />);
    for (let i = 0; i < 20; i++) {
      fireEvent.click(screen.getByTestId('zoom-in-btn'));
    }
    expect(screen.getByTestId('scale-display').textContent).toBe('400%');
  });

  it('calls onNodeClick with node id when an SVG node with data-node-id is clicked', () => {
    const onNodeClick = jest.fn();
    const { container } = render(<BlueprintViewer svgContent={mockSvg} onNodeClick={onNodeClick} />);
    const rect = container.querySelector('[data-node-id="node-1"]');
    expect(rect).toBeInTheDocument();
    fireEvent.click(rect!);
    expect(onNodeClick).toHaveBeenCalledWith('node-1');
  });

  it('calls onNodeClick with second node id', () => {
    const onNodeClick = jest.fn();
    const { container } = render(<BlueprintViewer svgContent={mockSvg} onNodeClick={onNodeClick} />);
    const circle = container.querySelector('[data-node-id="node-2"]');
    expect(circle).toBeInTheDocument();
    fireEvent.click(circle!);
    expect(onNodeClick).toHaveBeenCalledWith('node-2');
  });

  it('does not call onNodeClick when clicking outside SVG nodes', () => {
    const onNodeClick = jest.fn();
    render(<BlueprintViewer svgContent={mockSvg} onNodeClick={onNodeClick} />);
    const viewer = screen.getByTestId('blueprint-viewer');
    fireEvent.click(viewer);
    expect(onNodeClick).not.toHaveBeenCalled();
  });

  it('works without onNodeClick prop (no crash on node click)', () => {
    const { container } = render(<BlueprintViewer svgContent={mockSvg} />);
    const rect = container.querySelector('[data-node-id="node-1"]');
    expect(() => fireEvent.click(rect!)).not.toThrow();
  });
});
