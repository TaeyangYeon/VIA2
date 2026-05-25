import { useState } from 'react';
import { FileText, ChevronDown, ChevronRight, Save, Trash2, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../../store';
import { setDirectives } from '../../store/slices/directivesSlice';
import { saveDirectives } from '../../services/api';
import type { AgentDirectives } from '../../services/types';

interface AgentConfig {
  key: keyof AgentDirectives;
  label: string;
  placeholder: string;
}

const AGENTS: AgentConfig[] = [
  { key: 'orchestrator',     label: 'Orchestrator',      placeholder: 'Pipeline control & retry logic' },
  { key: 'spec',             label: 'Spec Agent',         placeholder: 'User text → mode/goal extraction' },
  { key: 'image_analysis',   label: 'Image Analysis',     placeholder: 'Visual feature detection & classification' },
  { key: 'depth',            label: 'Depth Agent',        placeholder: 'Depth estimation & 3D structure analysis' },
  { key: 'material',         label: 'Material Agent',     placeholder: 'Surface material & texture recognition' },
  { key: 'pipeline_composer',label: 'Pipeline Composer',  placeholder: 'Vision algorithm pipeline composition' },
  { key: 'vision_judge',     label: 'Vision Judge',       placeholder: 'Inspection result evaluation & scoring' },
  { key: 'inspection_plan',  label: 'Inspection Plan',    placeholder: 'Inspection strategy & test plan generation' },
  { key: 'test',             label: 'Test Agent',         placeholder: 'Algorithm validation & test execution' },
];

type SaveStatus = 'idle' | 'saving' | 'success' | 'error';

export default function DirectivePanel() {
  const dispatch = useAppDispatch();
  const stored = useAppSelector(s => s.directives);

  const [values, setValues] = useState<AgentDirectives>({ ...stored });
  const [expanded, setExpanded] = useState<Set<keyof AgentDirectives>>(new Set());
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle');

  const toggleExpand = (key: keyof AgentDirectives) => {
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  const handleSaveAll = async () => {
    setSaveStatus('saving');
    try {
      const result = await saveDirectives(values);
      dispatch(setDirectives(result));
      setSaveStatus('success');
      setTimeout(() => setSaveStatus('idle'), 3000);
    } catch {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 4000);
    }
  };

  const handleClearAll = () => {
    const cleared: AgentDirectives = {
      orchestrator: '', spec: '', image_analysis: '', depth: '', material: '',
      pipeline_composer: '', vision_judge: '', inspection_plan: '', test: '',
    };
    setValues(cleared);
  };

  return (
    <div
      data-testid="directive-panel"
      className="h-full overflow-y-auto p-6 flex flex-col gap-4"
    >
      {/* Header */}
      <div className="flex items-center gap-3">
        <FileText size={20} className="text-text-secondary" />
        <h2 className="text-base font-semibold text-text-primary">Agent Directives</h2>
      </div>

      <p className="text-xs text-text-disabled">
        Customize each agent's behavior. Leave empty to let the agent decide automatically.
      </p>

      {/* Agent cards */}
      <div className="flex flex-col gap-2">
        {AGENTS.map(({ key, label, placeholder }) => {
          const isExpanded = expanded.has(key);
          return (
            <div
              key={key}
              data-testid={`agent-card-${key}`}
              className="bg-white/5 backdrop-blur border border-white/10 rounded-lg overflow-hidden"
            >
              <button
                data-testid={`agent-header-${key}`}
                onClick={() => toggleExpand(key)}
                className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-white/5 transition-all duration-150"
              >
                <div className="flex items-center gap-2">
                  {isExpanded
                    ? <ChevronDown size={14} className="text-text-secondary" />
                    : <ChevronRight size={14} className="text-text-secondary" />
                  }
                  <span className="text-sm font-medium text-text-primary">{label}</span>
                  {values[key] === '' && (
                    <span className="text-xs text-text-disabled italic">auto</span>
                  )}
                </div>
                {values[key] !== '' && (
                  <span className="text-xs text-text-disabled truncate max-w-[200px]">
                    {values[key].substring(0, 40)}{values[key].length > 40 ? '…' : ''}
                  </span>
                )}
              </button>

              <div style={{ display: isExpanded ? 'block' : 'none' }}>
                <div className="px-4 pb-4">
                  <textarea
                    data-testid={`directive-textarea-${key}`}
                    value={values[key]}
                    onChange={e => setValues(prev => ({ ...prev, [key]: e.target.value }))}
                    placeholder={`${placeholder} — empty = agent decides automatically`}
                    rows={4}
                    className="w-full bg-black/30 border border-white/10 rounded px-3 py-2 text-sm text-text-primary placeholder:text-text-disabled focus:outline-none focus:border-white/30 transition-all duration-150 resize-y font-mono"
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Status feedback */}
      {saveStatus === 'success' && (
        <div data-testid="save-success" className="flex items-center gap-2 text-sm text-green-400">
          <CheckCircle size={14} />
          <span>All directives saved</span>
        </div>
      )}
      {saveStatus === 'error' && (
        <div data-testid="save-error" className="flex items-center gap-2 text-sm text-red-400">
          <XCircle size={14} />
          <span>Failed to save directives</span>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-3 pt-2">
        <button
          data-testid="clear-all-btn"
          onClick={handleClearAll}
          className="flex items-center gap-2 px-4 py-2 rounded bg-white/5 border border-white/10 text-sm text-text-secondary hover:bg-white/8 hover:text-text-primary transition-all duration-150"
        >
          <Trash2 size={14} />
          <span>Clear All</span>
        </button>

        <button
          data-testid="save-all-btn"
          onClick={handleSaveAll}
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
              <span>Save All</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
