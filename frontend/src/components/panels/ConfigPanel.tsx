import { useState } from 'react';
import { Settings, Save, CheckCircle, XCircle, Loader2, AlertTriangle } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../../store';
import { setConfig } from '../../store/slices/configSlice';
import { saveConfig } from '../../services/api';
import type { InspectionConfig } from '../../services/types';

type SaveStatus = 'idle' | 'saving' | 'success' | 'error';

function parseNullable(val: string): number | null {
  if (val === '') return null;
  const n = parseFloat(val);
  return isNaN(n) ? null : n;
}

function numToStr(val: number | null): string {
  return val != null ? String(val) : '';
}

export default function ConfigPanel() {
  const dispatch = useAppDispatch();
  const stored = useAppSelector(s => s.config);

  const [mode, setMode] = useState<'inspection' | 'align'>(stored.mode);
  const [maxIteration, setMaxIteration] = useState(String(stored.max_iteration));
  const [accuracy, setAccuracy] = useState(numToStr(stored.success_criteria.accuracy));
  const [fpRate, setFpRate] = useState(numToStr(stored.success_criteria.fp_rate));
  const [fnRate, setFnRate] = useState(numToStr(stored.success_criteria.fn_rate));
  const [coordError, setCoordError] = useState(numToStr(stored.success_criteria.coord_error));
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle');

  const accuracyVal = parseNullable(accuracy);
  const fpRateVal = parseNullable(fpRate);
  const fnRateVal = parseNullable(fnRate);
  const coordErrorVal = parseNullable(coordError);

  const showExtremeWarning =
    (accuracyVal != null && accuracyVal >= 0.99) ||
    (fpRateVal != null && fpRateVal <= 0.001) ||
    (fnRateVal != null && fnRateVal <= 0.001) ||
    (coordErrorVal != null && coordErrorVal <= 0.5);

  const buildConfig = (): InspectionConfig => ({
    mode,
    max_iteration: Math.min(10, Math.max(1, parseInt(maxIteration, 10) || 3)),
    success_criteria: {
      accuracy: mode === 'inspection' ? accuracyVal : null,
      fp_rate: mode === 'inspection' ? fpRateVal : null,
      fn_rate: mode === 'inspection' ? fnRateVal : null,
      coord_error: mode === 'align' ? coordErrorVal : null,
    },
  });

  const handleSave = async () => {
    setSaveStatus('saving');
    try {
      const result = await saveConfig(buildConfig());
      dispatch(setConfig({
        mode: result.mode,
        max_iteration: result.max_iteration,
        success_criteria: result.success_criteria,
      }));
      setSaveStatus('success');
      setTimeout(() => setSaveStatus('idle'), 3000);
    } catch {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 4000);
    }
  };

  return (
    <div data-testid="config-panel" className="h-full overflow-y-auto p-6 flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Settings size={20} className="text-text-secondary" />
        <h2 className="text-base font-semibold text-text-primary">Configuration</h2>
      </div>

      {/* Mode toggle */}
      <div className="bg-white/5 backdrop-blur border border-white/10 rounded-lg p-4 flex flex-col gap-4">
        <p className="text-xs font-medium text-text-secondary uppercase tracking-wider">Mode</p>
        <div className="flex gap-5">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              data-testid="mode-inspection"
              type="radio"
              name="config-mode"
              value="inspection"
              checked={mode === 'inspection'}
              onChange={() => setMode('inspection')}
              className="accent-white"
            />
            <span className="text-sm text-text-primary">Inspection</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              data-testid="mode-align"
              type="radio"
              name="config-mode"
              value="align"
              checked={mode === 'align'}
              onChange={() => setMode('align')}
              className="accent-white"
            />
            <span className="text-sm text-text-primary">Align</span>
          </label>
        </div>
      </div>

      {/* Max iteration */}
      <div className="bg-white/5 backdrop-blur border border-white/10 rounded-lg p-4 flex flex-col gap-3">
        <p className="text-xs font-medium text-text-secondary uppercase tracking-wider">Max Iteration</p>
        <input
          data-testid="max-iteration-input"
          type="number"
          min={1}
          max={10}
          value={maxIteration}
          onChange={e => setMaxIteration(e.target.value)}
          className="bg-black/30 border border-white/10 rounded px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-white/30 transition-all duration-150 w-24"
        />
        <p className="text-xs text-text-disabled">Range: 1–10</p>
      </div>

      {/* Success criteria */}
      <div className="bg-white/5 backdrop-blur border border-white/10 rounded-lg p-4 flex flex-col gap-4">
        <p className="text-xs font-medium text-text-secondary uppercase tracking-wider">Success Criteria</p>
        <p className="text-xs text-text-disabled">Leave empty to let the system decide.</p>

        {mode === 'inspection' && (
          <div className="flex flex-col gap-3">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs text-text-secondary">Accuracy (0–1)</label>
              <input
                data-testid="accuracy-input"
                type="number"
                min={0}
                max={1}
                step={0.001}
                value={accuracy}
                onChange={e => setAccuracy(e.target.value)}
                placeholder="null"
                className="bg-black/30 border border-white/10 rounded px-3 py-2 text-sm text-text-primary placeholder:text-text-disabled focus:outline-none focus:border-white/30 transition-all duration-150"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-xs text-text-secondary">FP Rate (0–1)</label>
              <input
                data-testid="fp-rate-input"
                type="number"
                min={0}
                max={1}
                step={0.001}
                value={fpRate}
                onChange={e => setFpRate(e.target.value)}
                placeholder="null"
                className="bg-black/30 border border-white/10 rounded px-3 py-2 text-sm text-text-primary placeholder:text-text-disabled focus:outline-none focus:border-white/30 transition-all duration-150"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-xs text-text-secondary">FN Rate (0–1)</label>
              <input
                data-testid="fn-rate-input"
                type="number"
                min={0}
                max={1}
                step={0.001}
                value={fnRate}
                onChange={e => setFnRate(e.target.value)}
                placeholder="null"
                className="bg-black/30 border border-white/10 rounded px-3 py-2 text-sm text-text-primary placeholder:text-text-disabled focus:outline-none focus:border-white/30 transition-all duration-150"
              />
            </div>
          </div>
        )}

        {mode === 'align' && (
          <div className="flex flex-col gap-3">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs text-text-secondary">Coord Error (px)</label>
              <input
                data-testid="coord-error-input"
                type="number"
                min={0}
                step={0.1}
                value={coordError}
                onChange={e => setCoordError(e.target.value)}
                placeholder="null"
                className="bg-black/30 border border-white/10 rounded px-3 py-2 text-sm text-text-primary placeholder:text-text-disabled focus:outline-none focus:border-white/30 transition-all duration-150"
              />
            </div>
          </div>
        )}
      </div>

      {/* Extreme goal warning */}
      {showExtremeWarning && (
        <div
          data-testid="extreme-goal-warning"
          className="flex items-start gap-2 p-3 rounded-lg border"
          style={{
            background: 'rgba(250,204,21,0.08)',
            borderColor: 'rgba(250,204,21,0.3)',
            color: '#facc15',
          }}
        >
          <AlertTriangle size={14} className="flex-shrink-0 mt-0.5" />
          <span className="text-xs">
            Extreme goal detected. These thresholds may be unreachable and could cause excessive iteration.
          </span>
        </div>
      )}

      {/* Status feedback */}
      {saveStatus === 'success' && (
        <div data-testid="save-success" className="flex items-center gap-2 text-sm text-green-400">
          <CheckCircle size={14} />
          <span>Configuration saved</span>
        </div>
      )}
      {saveStatus === 'error' && (
        <div data-testid="save-error" className="flex items-center gap-2 text-sm text-red-400">
          <XCircle size={14} />
          <span>Failed to save configuration</span>
        </div>
      )}

      {/* Save button */}
      <div>
        <button
          data-testid="save-btn"
          onClick={handleSave}
          disabled={saveStatus === 'saving'}
          className="flex items-center gap-2 px-4 py-2 rounded bg-white/10 border border-white/15 text-sm text-text-primary hover:bg-white/15 transition-all duration-150 disabled:opacity-50"
        >
          {saveStatus === 'saving' ? (
            <>
              <Loader2 size={14} className="animate-spin" />
              <span data-testid="save-loading">Saving...</span>
            </>
          ) : (
            <>
              <Save size={14} />
              <span>Save</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
