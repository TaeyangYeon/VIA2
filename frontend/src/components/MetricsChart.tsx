import { CheckCircle, XCircle } from 'lucide-react';

interface ItemResult {
  item_id: string;
  category: string;
  passed: boolean;
  accuracy: number;
  fp_rate: number;
  fn_rate: number;
}

interface Props {
  itemResults: object[];
}

export default function MetricsChart({ itemResults }: Props) {
  const items = itemResults as ItemResult[];
  const totalCount = items.length;
  const passedCount = items.filter(i => i.passed).length;
  const failedCount = totalCount - passedCount;

  return (
    <div
      data-testid="metrics-table"
      className="bg-white/5 backdrop-blur border border-white/10 rounded-lg overflow-hidden"
    >
      <div className="px-4 py-3 border-b border-white/10">
        <p className="text-xs font-medium text-text-secondary uppercase tracking-wider">
          Inspection Results
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-white/10">
              <th className="px-4 py-2.5 text-left text-text-disabled font-medium">Item ID</th>
              <th className="px-4 py-2.5 text-left text-text-disabled font-medium">Category</th>
              <th className="px-4 py-2.5 text-left text-text-disabled font-medium">Status</th>
              <th className="px-4 py-2.5 text-right text-text-disabled font-medium">Accuracy</th>
              <th className="px-4 py-2.5 text-left text-text-disabled font-medium" style={{ width: '120px' }}>
                FP Rate
              </th>
              <th className="px-4 py-2.5 text-left text-text-disabled font-medium" style={{ width: '120px' }}>
                FN Rate
              </th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, index) => (
              <tr key={index} className="border-b border-white/5 transition-all duration-150">
                <td className="px-4 py-2.5 text-text-primary font-mono">{item.item_id}</td>
                <td className="px-4 py-2.5 text-text-secondary">{item.category}</td>
                <td className="px-4 py-2.5">
                  {item.passed ? (
                    <span
                      data-testid={`status-passed-${item.item_id}`}
                      className="flex items-center gap-1"
                      style={{ color: '#4ade80' }}
                    >
                      <CheckCircle size={12} />
                      <span>Pass</span>
                    </span>
                  ) : (
                    <span
                      data-testid={`status-failed-${item.item_id}`}
                      className="flex items-center gap-1"
                      style={{ color: '#f87171' }}
                    >
                      <XCircle size={12} />
                      <span>Fail</span>
                    </span>
                  )}
                </td>
                <td className="px-4 py-2.5 text-right text-text-primary">
                  {(item.accuracy * 100).toFixed(1)}%
                </td>
                <td className="px-4 py-2.5">
                  <div className="flex items-center gap-1.5">
                    <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
                      <div
                        data-testid={`fp-bar-${item.item_id}`}
                        className="h-full rounded-full"
                        style={{ width: `${item.fp_rate * 100}%`, background: '#f87171' }}
                      />
                    </div>
                    <span className="text-text-disabled" style={{ width: '36px', textAlign: 'right', flexShrink: 0 }}>
                      {(item.fp_rate * 100).toFixed(1)}%
                    </span>
                  </div>
                </td>
                <td className="px-4 py-2.5">
                  <div className="flex items-center gap-1.5">
                    <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
                      <div
                        data-testid={`fn-bar-${item.item_id}`}
                        className="h-full rounded-full"
                        style={{ width: `${item.fn_rate * 100}%`, background: '#facc15' }}
                      />
                    </div>
                    <span className="text-text-disabled" style={{ width: '36px', textAlign: 'right', flexShrink: 0 }}>
                      {(item.fn_rate * 100).toFixed(1)}%
                    </span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr
              data-testid="metrics-summary-row"
              className="border-t border-white/10"
              style={{ background: 'rgba(255,255,255,0.03)' }}
            >
              <td className="px-4 py-2.5 text-text-secondary font-medium" colSpan={2}>
                Total
              </td>
              <td className="px-4 py-2.5">
                <div className="flex items-center gap-2">
                  <span style={{ color: '#4ade80' }}>{passedCount} pass</span>
                  <span className="text-text-disabled">/</span>
                  <span style={{ color: '#f87171' }}>{failedCount} fail</span>
                </div>
              </td>
              <td className="px-4 py-2.5 text-right text-text-secondary">
                {totalCount > 0 ? `${passedCount}/${totalCount}` : '—'}
              </td>
              <td colSpan={2} />
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}
