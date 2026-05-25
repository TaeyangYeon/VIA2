import { useState } from 'react';
import { Cpu, Wifi, Save, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../../store';
import { setEngine } from '../../store/slices/engineSlice';
import { getEngine, updateEngine } from '../../services/api';
import type { EngineSettings } from '../../services/types';

type SaveStatus = 'idle' | 'saving' | 'success' | 'error';
type TestStatus = 'idle' | 'testing' | 'success' | 'error';

export default function EnginePanel() {
  const dispatch = useAppDispatch();
  const stored = useAppSelector(s => s.engine);

  const [mode, setMode] = useState<'local' | 'remote'>(stored.mode);
  const [localOllamaUrl, setLocalOllamaUrl] = useState(stored.local_ollama_url);
  const [modelName, setModelName] = useState(stored.model_name);
  const [remoteType, setRemoteType] = useState(stored.remote_type);
  const [remoteUrl, setRemoteUrl] = useState(stored.remote_url ?? '');
  const [remoteAuthToken, setRemoteAuthToken] = useState(stored.remote_auth_token ?? '');

  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle');
  const [testStatus, setTestStatus] = useState<TestStatus>('idle');

  const buildSettings = (): EngineSettings => ({
    mode,
    local_ollama_url: localOllamaUrl,
    model_name: modelName,
    remote_type: remoteType,
    remote_url: remoteUrl || null,
    remote_auth_token: remoteAuthToken || null,
  });

  const handleSave = async () => {
    setSaveStatus('saving');
    try {
      const result = await updateEngine(buildSettings());
      dispatch(setEngine(result));
      setSaveStatus('success');
      setTimeout(() => setSaveStatus('idle'), 3000);
    } catch {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 4000);
    }
  };

  const handleTestConnection = async () => {
    setTestStatus('testing');
    try {
      await getEngine();
      setTestStatus('success');
      setTimeout(() => setTestStatus('idle'), 3000);
    } catch {
      setTestStatus('error');
      setTimeout(() => setTestStatus('idle'), 4000);
    }
  };

  return (
    <div
      data-testid="engine-panel"
      className="h-full overflow-y-auto p-6 flex flex-col gap-6"
    >
      {/* Header */}
      <div className="flex items-center gap-3">
        <Cpu size={20} className="text-text-secondary" />
        <h2 className="text-base font-semibold text-text-primary">Engine Settings</h2>
      </div>

      {/* Mode selector */}
      <div className="bg-white/5 backdrop-blur border border-white/10 rounded-lg p-4 flex flex-col gap-4">
        <p className="text-xs font-medium text-text-secondary uppercase tracking-wider">Mode</p>
        <div className="flex gap-3">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              data-testid="mode-local"
              type="radio"
              name="engine-mode"
              value="local"
              checked={mode === 'local'}
              onChange={() => setMode('local')}
              className="accent-white"
            />
            <span className="text-sm text-text-primary">Local (Ollama)</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              data-testid="mode-remote"
              type="radio"
              name="engine-mode"
              value="remote"
              checked={mode === 'remote'}
              onChange={() => setMode('remote')}
              className="accent-white"
            />
            <span className="text-sm text-text-primary">Remote</span>
          </label>
        </div>
      </div>

      {/* Local fields */}
      {mode === 'local' && (
        <div className="bg-white/5 backdrop-blur border border-white/10 rounded-lg p-4 flex flex-col gap-4">
          <p className="text-xs font-medium text-text-secondary uppercase tracking-wider">Local Configuration</p>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-text-secondary">Ollama URL</label>
            <input
              data-testid="local-ollama-url-input"
              type="text"
              value={localOllamaUrl}
              onChange={e => setLocalOllamaUrl(e.target.value)}
              placeholder="http://127.0.0.1:11434"
              className="bg-black/30 border border-white/10 rounded px-3 py-2 text-sm text-text-primary placeholder:text-text-disabled focus:outline-none focus:border-white/30 transition-all duration-150"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-text-secondary">Model Name</label>
            <input
              data-testid="model-name-input"
              type="text"
              value={modelName}
              onChange={e => setModelName(e.target.value)}
              placeholder="qwen2.5-coder:7b"
              className="bg-black/30 border border-white/10 rounded px-3 py-2 text-sm text-text-primary placeholder:text-text-disabled focus:outline-none focus:border-white/30 transition-all duration-150"
            />
          </div>
        </div>
      )}

      {/* Remote fields */}
      {mode === 'remote' && (
        <div className="bg-white/5 backdrop-blur border border-white/10 rounded-lg p-4 flex flex-col gap-4">
          <p className="text-xs font-medium text-text-secondary uppercase tracking-wider">Remote Configuration</p>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-text-secondary">Provider Type</label>
            <select
              data-testid="remote-type-select"
              value={remoteType}
              onChange={e => setRemoteType(e.target.value)}
              className="bg-black/30 border border-white/10 rounded px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-white/30 transition-all duration-150"
            >
              <option value="colab">Google Colab</option>
              <option value="azure">Azure</option>
              <option value="custom">Custom</option>
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-text-secondary">Remote URL</label>
            <input
              data-testid="remote-url-input"
              type="text"
              value={remoteUrl}
              onChange={e => setRemoteUrl(e.target.value)}
              placeholder="https://your-endpoint.example.com"
              className="bg-black/30 border border-white/10 rounded px-3 py-2 text-sm text-text-primary placeholder:text-text-disabled focus:outline-none focus:border-white/30 transition-all duration-150"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-text-secondary">Auth Token</label>
            <input
              data-testid="remote-auth-token-input"
              type="password"
              value={remoteAuthToken}
              onChange={e => setRemoteAuthToken(e.target.value)}
              placeholder="Bearer token or API key"
              className="bg-black/30 border border-white/10 rounded px-3 py-2 text-sm text-text-primary placeholder:text-text-disabled focus:outline-none focus:border-white/30 transition-all duration-150"
            />
          </div>
        </div>
      )}

      {/* Status feedback */}
      {(saveStatus !== 'idle' || testStatus !== 'idle') && (
        <div className="flex flex-col gap-2">
          {saveStatus === 'success' && (
            <div data-testid="save-success" className="flex items-center gap-2 text-sm text-green-400">
              <CheckCircle size={14} />
              <span>Settings saved successfully</span>
            </div>
          )}
          {saveStatus === 'error' && (
            <div data-testid="save-error" className="flex items-center gap-2 text-sm text-red-400">
              <XCircle size={14} />
              <span>Failed to save settings</span>
            </div>
          )}
          {testStatus === 'success' && (
            <div data-testid="connection-success" className="flex items-center gap-2 text-sm text-green-400">
              <CheckCircle size={14} />
              <span>Connection successful</span>
            </div>
          )}
          {testStatus === 'error' && (
            <div data-testid="connection-error" className="flex items-center gap-2 text-sm text-red-400">
              <XCircle size={14} />
              <span>Connection failed</span>
            </div>
          )}
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-3">
        <button
          data-testid="test-connection-btn"
          onClick={handleTestConnection}
          disabled={testStatus === 'testing'}
          className="flex items-center gap-2 px-4 py-2 rounded bg-white/8 border border-white/10 text-sm text-text-primary hover:bg-white/12 transition-all duration-150 disabled:opacity-50"
        >
          {testStatus === 'testing' ? (
            <Loader2 size={14} className="animate-spin" />
          ) : (
            <Wifi size={14} />
          )}
          <span>Test Connection</span>
        </button>

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
