import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import ExportButton from '../components/ExportButton';
import * as exportApi from '../services/export_api';

jest.mock('../services/export_api');

const mockExportSVG = exportApi.exportSVG as jest.MockedFunction<typeof exportApi.exportSVG>;
const mockExportPDF = exportApi.exportPDF as jest.MockedFunction<typeof exportApi.exportPDF>;
const mockExportParameters = exportApi.exportParameters as jest.MockedFunction<typeof exportApi.exportParameters>;

function makeBlob(content = 'mock') {
  return new Blob([content], { type: 'application/octet-stream' });
}

describe('ExportButton', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    Object.defineProperty(global.URL, 'createObjectURL', {
      writable: true,
      value: jest.fn(() => 'blob:mock-url'),
    });
    Object.defineProperty(global.URL, 'revokeObjectURL', {
      writable: true,
      value: jest.fn(),
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  // ── render ──────────────────────────────────────────────────────────────────

  it('renders export-panel wrapper', () => {
    render(<ExportButton executionId="exec-1" />);
    expect(screen.getByTestId('export-panel')).toBeInTheDocument();
  });

  it('renders all three buttons', () => {
    render(<ExportButton executionId="exec-1" />);
    expect(screen.getByTestId('export-svg-btn')).toBeInTheDocument();
    expect(screen.getByTestId('export-pdf-btn')).toBeInTheDocument();
    expect(screen.getByTestId('export-params-btn')).toBeInTheDocument();
  });

  it('does not show error on initial render', () => {
    render(<ExportButton executionId="exec-1" />);
    expect(screen.queryByTestId('export-error')).not.toBeInTheDocument();
  });

  it('does not show loading indicator on initial render', () => {
    render(<ExportButton executionId="exec-1" />);
    expect(screen.queryByTestId('export-loading')).not.toBeInTheDocument();
  });

  // ── null executionId → error ─────────────────────────────────────────────

  it('shows export-error when export-svg-btn clicked with null executionId', () => {
    render(<ExportButton executionId={null} />);
    fireEvent.click(screen.getByTestId('export-svg-btn'));
    expect(screen.getByTestId('export-error')).toBeInTheDocument();
  });

  it('shows export-error when export-pdf-btn clicked with null executionId', () => {
    render(<ExportButton executionId={null} />);
    fireEvent.click(screen.getByTestId('export-pdf-btn'));
    expect(screen.getByTestId('export-error')).toBeInTheDocument();
  });

  it('shows export-error when export-params-btn clicked with null executionId', () => {
    render(<ExportButton executionId={null} />);
    fireEvent.click(screen.getByTestId('export-params-btn'));
    expect(screen.getByTestId('export-error')).toBeInTheDocument();
  });

  it('does not call exportSVG when executionId is null', () => {
    render(<ExportButton executionId={null} />);
    fireEvent.click(screen.getByTestId('export-svg-btn'));
    expect(mockExportSVG).not.toHaveBeenCalled();
  });

  // ── SVG export ────────────────────────────────────────────────────────────

  it('calls exportSVG with executionId when export-svg-btn clicked', async () => {
    mockExportSVG.mockResolvedValueOnce(makeBlob('<svg/>'));
    render(<ExportButton executionId="exec-123" />);
    await act(async () => {
      fireEvent.click(screen.getByTestId('export-svg-btn'));
    });
    expect(mockExportSVG).toHaveBeenCalledWith('exec-123');
  });

  it('triggers download (URL.createObjectURL) after successful SVG export', async () => {
    mockExportSVG.mockResolvedValueOnce(makeBlob('<svg/>'));
    render(<ExportButton executionId="exec-1" />);
    await act(async () => {
      fireEvent.click(screen.getByTestId('export-svg-btn'));
    });
    expect(global.URL.createObjectURL).toHaveBeenCalled();
    expect(global.URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-url');
  });

  it('shows export-error when SVG export API fails', async () => {
    mockExportSVG.mockRejectedValueOnce(new Error('network error'));
    render(<ExportButton executionId="exec-1" />);
    await act(async () => {
      fireEvent.click(screen.getByTestId('export-svg-btn'));
    });
    await waitFor(() => {
      expect(screen.getByTestId('export-error')).toBeInTheDocument();
    });
  });

  // ── PDF export ────────────────────────────────────────────────────────────

  it('calls exportPDF with executionId when export-pdf-btn clicked', async () => {
    mockExportPDF.mockResolvedValueOnce(makeBlob('%PDF-1.4'));
    render(<ExportButton executionId="exec-456" />);
    await act(async () => {
      fireEvent.click(screen.getByTestId('export-pdf-btn'));
    });
    expect(mockExportPDF).toHaveBeenCalledWith('exec-456');
  });

  it('triggers download after successful PDF export', async () => {
    mockExportPDF.mockResolvedValueOnce(makeBlob('%PDF'));
    render(<ExportButton executionId="exec-1" />);
    await act(async () => {
      fireEvent.click(screen.getByTestId('export-pdf-btn'));
    });
    expect(global.URL.createObjectURL).toHaveBeenCalled();
  });

  // ── Parameters export ─────────────────────────────────────────────────────

  it('calls exportParameters with executionId when export-params-btn clicked', async () => {
    mockExportParameters.mockResolvedValueOnce({ parameter_sheets: [] });
    render(<ExportButton executionId="exec-789" />);
    await act(async () => {
      fireEvent.click(screen.getByTestId('export-params-btn'));
    });
    expect(mockExportParameters).toHaveBeenCalledWith('exec-789');
  });

  it('triggers download after successful parameters export', async () => {
    mockExportParameters.mockResolvedValueOnce({ parameter_sheets: [{ node_id: 'n1' }] });
    render(<ExportButton executionId="exec-1" />);
    await act(async () => {
      fireEvent.click(screen.getByTestId('export-params-btn'));
    });
    expect(global.URL.createObjectURL).toHaveBeenCalled();
  });

  it('shows export-error when parameters export API fails', async () => {
    mockExportParameters.mockRejectedValueOnce(new Error('not found'));
    render(<ExportButton executionId="exec-1" />);
    await act(async () => {
      fireEvent.click(screen.getByTestId('export-params-btn'));
    });
    await waitFor(() => {
      expect(screen.getByTestId('export-error')).toBeInTheDocument();
    });
  });

  // ── loading state ─────────────────────────────────────────────────────────

  it('shows export-loading while SVG export is in progress', async () => {
    let resolve: (v: Blob) => void = () => {};
    mockExportSVG.mockReturnValueOnce(new Promise<Blob>(r => { resolve = r; }));
    render(<ExportButton executionId="exec-1" />);
    await act(async () => {
      fireEvent.click(screen.getByTestId('export-svg-btn'));
    });
    expect(screen.getByTestId('export-loading')).toBeInTheDocument();
    await act(async () => { resolve(makeBlob()); });
  });

  it('hides export-loading after SVG export completes', async () => {
    mockExportSVG.mockResolvedValueOnce(makeBlob('<svg/>'));
    render(<ExportButton executionId="exec-1" />);
    await act(async () => {
      fireEvent.click(screen.getByTestId('export-svg-btn'));
    });
    await waitFor(() => {
      expect(screen.queryByTestId('export-loading')).not.toBeInTheDocument();
    });
  });
});
