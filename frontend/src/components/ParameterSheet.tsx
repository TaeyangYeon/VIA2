import { X } from 'lucide-react';

interface Props {
  isOpen: boolean;
  nodeId: string | null;
  data: Record<string, unknown> | null;
  onClose: () => void;
}

function renderValue(value: unknown): string {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

export default function ParameterSheet({ isOpen, nodeId, data, onClose }: Props) {
  const rawNode = nodeId && data ? (data as Record<string, unknown>)[nodeId] : null;
  const nodeData =
    rawNode && typeof rawNode === 'object' ? (rawNode as Record<string, unknown>) : null;
  const entries = nodeData ? Object.entries(nodeData) : [];

  return (
    <div
      data-testid="parameter-sheet"
      style={{ display: isOpen ? 'flex' : 'none' }}
      className="w-64 flex-shrink-0 bg-white/5 backdrop-blur border border-white/10 rounded-lg flex-col overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 flex-shrink-0">
        <div className="min-w-0">
          <p className="text-xs font-medium text-text-secondary uppercase tracking-wider">
            Parameters
          </p>
          {nodeId && (
            <p
              data-testid="parameter-node-id"
              className="text-xs text-text-disabled mt-0.5 font-mono truncate"
            >
              {nodeId}
            </p>
          )}
        </div>
        <button
          data-testid="parameter-close-btn"
          onClick={onClose}
          className="w-6 h-6 flex items-center justify-center rounded hover:bg-white/10 text-text-disabled hover:text-text-primary transition-all duration-150 flex-shrink-0 ml-2"
        >
          <X size={12} />
        </button>
      </div>

      {/* Parameter entries */}
      <div className="flex-1 overflow-y-auto p-3">
        {entries.length === 0 ? (
          <p className="text-xs text-text-disabled text-center py-4">No parameters available</p>
        ) : (
          <div className="flex flex-col gap-3">
            {entries.map(([key, value]) => (
              <div key={key} className="flex flex-col gap-0.5">
                <span className="text-xs text-text-secondary font-medium">{key}</span>
                <span
                  data-testid={`param-value-${key}`}
                  className="text-xs text-text-primary font-mono break-all"
                >
                  {renderValue(value)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
