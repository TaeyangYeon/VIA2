import { useState } from 'react';
import { BarChart2, Download, FileText } from 'lucide-react';
import { useAppSelector } from '../../store';
import BlueprintViewer from '../BlueprintViewer';
import ParameterSheet from '../ParameterSheet';
import MetricsChart from '../MetricsChart';
import LightingSuggestion from '../LightingSuggestion';
import ExportButton from '../ExportButton';

const DECISION_LABELS: Record<string, { label: string; color: string }> = {
  rule_based_ok:  { label: 'Rule-Based OK',                 color: '#4ade80' },
  edge_learning:  { label: 'Edge Learning Required',         color: '#facc15' },
  deep_learning:  { label: 'Deep Learning Required',         color: '#60a5fa' },
  hw_improvement: { label: 'Hardware Improvement Required',  color: '#f87171' },
};

export default function ResultPanel() {
  const result = useAppSelector(s => s.result);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const executionId: string | null = useAppSelector((s: any) => s.execution?.execution_id ?? null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  const hasResult =
    result.summary !== null ||
    result.blueprint_svg !== null ||
    result.decision !== null;

  const handleExportSvg = () => {
    if (!result.blueprint_svg) return;
    const blob = new Blob([result.blueprint_svg], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'blueprint.svg';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportPdf = () => {
    window.alert('PDF export coming soon');
  };

  if (!hasResult) {
    return (
      <div data-testid="result-panel" className="h-full flex items-center justify-center">
        <div data-testid="result-empty-state" className="flex flex-col items-center gap-3 text-center">
          <BarChart2 size={32} className="text-text-disabled" />
          <p className="text-sm text-text-disabled">No results yet. Run execution to see results.</p>
        </div>
      </div>
    );
  }

  const decisionInfo = result.decision ? DECISION_LABELS[result.decision] ?? null : null;

  return (
    <div data-testid="result-panel" className="h-full overflow-y-auto p-6 flex flex-col gap-6">
      {/* Header + export buttons */}
      <div className="flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <BarChart2 size={20} className="text-text-secondary" />
          <h2 className="text-base font-semibold text-text-primary">Result</h2>
        </div>
        <div className="flex items-center gap-2">
          {result.blueprint_svg && (
            <button
              data-testid="export-svg-btn"
              onClick={handleExportSvg}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-white/5 border border-white/10 text-xs text-text-secondary hover:bg-white/8 hover:text-text-primary transition-all duration-150"
            >
              <Download size={12} />
              <span>Export SVG</span>
            </button>
          )}
          <button
            data-testid="export-pdf-btn"
            onClick={handleExportPdf}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-white/5 border border-white/10 text-xs text-text-secondary hover:bg-white/8 hover:text-text-primary transition-all duration-150"
          >
            <FileText size={12} />
            <span>Export PDF</span>
          </button>
        </div>
      </div>

      {/* Decision card */}
      {result.decision && decisionInfo && (
        <div
          data-testid="decision-card"
          className="rounded-lg p-4 border"
          style={{
            background: `${decisionInfo.color}14`,
            borderColor: `${decisionInfo.color}40`,
          }}
        >
          <p className="text-xs font-medium text-text-secondary uppercase tracking-wider mb-2">
            Decision
          </p>
          <p className="text-sm font-semibold" style={{ color: decisionInfo.color }}>
            {decisionInfo.label}
          </p>
          {result.decision_reason && (
            <p data-testid="decision-reason" className="text-xs text-text-secondary mt-2">
              {result.decision_reason}
            </p>
          )}
        </div>
      )}

      {/* Summary */}
      {result.summary && (
        <div className="bg-white/5 backdrop-blur border border-white/10 rounded-lg p-4">
          <p className="text-xs font-medium text-text-secondary uppercase tracking-wider mb-2">
            Summary
          </p>
          <p data-testid="result-summary" className="text-sm text-text-primary leading-relaxed">
            {result.summary}
          </p>
        </div>
      )}

      {/* Blueprint viewer */}
      {result.blueprint_svg && (
        <div className="flex gap-4 min-h-0">
          <div className="flex-1 min-w-0">
            <BlueprintViewer
              svgContent={result.blueprint_svg}
              onNodeClick={setSelectedNodeId}
            />
          </div>
          <ParameterSheet
            isOpen={selectedNodeId !== null}
            nodeId={selectedNodeId}
            data={result.parameter_sheet as Record<string, unknown> | null}
            onClose={() => setSelectedNodeId(null)}
          />
        </div>
      )}

      {/* Metrics table */}
      {result.item_results && result.item_results.length > 0 && (
        <MetricsChart itemResults={result.item_results} />
      )}

      {/* Lighting suggestions */}
      {result.lighting_suggestions && result.lighting_suggestions.length > 0 && (
        <LightingSuggestion suggestions={result.lighting_suggestions} />
      )}

      {/* Improvement suggestions */}
      {result.improvement_suggestions && result.improvement_suggestions.length > 0 && (
        <div className="bg-white/5 backdrop-blur border border-white/10 rounded-lg p-4 flex flex-col gap-3">
          <p className="text-xs font-medium text-text-secondary uppercase tracking-wider">
            Improvement Suggestions
          </p>
          <ul className="flex flex-col gap-2">
            {result.improvement_suggestions.map((s, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-text-secondary">
                <span className="text-text-disabled mt-0.5 flex-shrink-0">•</span>
                <span>{s}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* API-based export (available after pipeline run) */}
      {executionId && <ExportButton executionId={executionId} />}
    </div>
  );
}
