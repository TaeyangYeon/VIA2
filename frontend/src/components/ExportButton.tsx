import { useState } from 'react';
import { Download, FileText, Table } from 'lucide-react';
import { exportSVG, exportPDF, exportParameters } from '../services/export_api';

interface ExportButtonProps {
  executionId: string | null;
}

export default function ExportButton({ executionId }: ExportButtonProps) {
  const [svgLoading, setSvgLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [paramsLoading, setParamsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isLoading = svgLoading || pdfLoading || paramsLoading;

  const triggerDownload = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportSvg = async () => {
    if (!executionId) {
      setError('No execution ID. Run pipeline first to export.');
      return;
    }
    setError(null);
    setSvgLoading(true);
    try {
      const blob = await exportSVG(executionId);
      triggerDownload(blob, 'blueprint.svg');
    } catch {
      setError('SVG export failed. Check execution result.');
    } finally {
      setSvgLoading(false);
    }
  };

  const handleExportPdf = async () => {
    if (!executionId) {
      setError('No execution ID. Run pipeline first to export.');
      return;
    }
    setError(null);
    setPdfLoading(true);
    try {
      const blob = await exportPDF(executionId);
      triggerDownload(blob, 'blueprint.pdf');
    } catch {
      setError('PDF export failed. Check execution result.');
    } finally {
      setPdfLoading(false);
    }
  };

  const handleExportParams = async () => {
    if (!executionId) {
      setError('No execution ID. Run pipeline first to export.');
      return;
    }
    setError(null);
    setParamsLoading(true);
    try {
      const data = await exportParameters(executionId);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      triggerDownload(blob, 'parameters.json');
    } catch {
      setError('Parameter export failed. Check execution result.');
    } finally {
      setParamsLoading(false);
    }
  };

  return (
    <div
      data-testid="export-panel"
      className="bg-white/5 backdrop-blur border border-white/10 rounded-lg p-4 flex flex-col gap-3"
    >
      <p className="text-xs font-medium text-text-secondary uppercase tracking-wider">
        Export Results
      </p>
      {isLoading && (
        <p data-testid="export-loading" className="text-xs text-text-secondary animate-pulse">
          Exporting…
        </p>
      )}
      {error && (
        <p data-testid="export-error" className="text-xs" style={{ color: '#f87171' }}>
          {error}
        </p>
      )}
      <div className="flex flex-wrap gap-2">
        <button
          data-testid="export-svg-btn"
          onClick={handleExportSvg}
          disabled={svgLoading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-white/5 border border-white/10 text-xs text-text-secondary hover:text-text-primary transition-all duration-150 disabled:opacity-50"
        >
          <Download size={12} />
          <span>{svgLoading ? 'Exporting…' : 'Export SVG'}</span>
        </button>
        <button
          data-testid="export-pdf-btn"
          onClick={handleExportPdf}
          disabled={pdfLoading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-white/5 border border-white/10 text-xs text-text-secondary hover:text-text-primary transition-all duration-150 disabled:opacity-50"
        >
          <FileText size={12} />
          <span>{pdfLoading ? 'Exporting…' : 'Export PDF'}</span>
        </button>
        <button
          data-testid="export-params-btn"
          onClick={handleExportParams}
          disabled={paramsLoading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-white/5 border border-white/10 text-xs text-text-secondary hover:text-text-primary transition-all duration-150 disabled:opacity-50"
        >
          <Table size={12} />
          <span>{paramsLoading ? 'Exporting…' : 'Export Parameters (JSON)'}</span>
        </button>
      </div>
    </div>
  );
}
