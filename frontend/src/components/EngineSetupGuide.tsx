import { useState } from 'react';

interface EngineSetupGuideProps {
  isOpen: boolean;
  engineMode: 'local' | 'remote';
  remoteUrl?: string;
  onClose: () => void;
  onRetry: () => void;
}

interface CopyableCommandProps {
  command: string;
}

function CopyableCommand({ command }: CopyableCommandProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(command);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard unavailable
    }
  };

  return (
    <div className="flex items-center gap-2 bg-gray-800 rounded px-3 py-2 font-mono text-sm">
      <code className="flex-1 text-green-400">{command}</code>
      <button
        onClick={handleCopy}
        className="text-xs text-gray-400 hover:text-gray-200 transition-colors shrink-0"
      >
        {copied ? 'Copied!' : 'Copy'}
      </button>
    </div>
  );
}

export default function EngineSetupGuide({
  isOpen,
  engineMode,
  remoteUrl,
  onClose,
  onRetry,
}: EngineSetupGuideProps) {
  const [editedUrl, setEditedUrl] = useState(remoteUrl ?? '');

  if (!isOpen) return null;

  return (
    <div
      data-testid="engine-setup-guide"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
    >
      <div className="bg-gray-900 border border-white/10 rounded-xl shadow-2xl w-full max-w-lg mx-4 p-6">
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-gray-100">AI Engine Unreachable</h2>
          <p className="mt-1 text-sm text-gray-400">
            VIA2 could not connect to the AI engine. Follow the steps below to get started.
          </p>
        </div>

        <div
          data-testid="engine-setup-mode-label"
          className="mb-4 inline-block px-2 py-0.5 rounded text-xs font-medium bg-white/10 text-gray-300"
        >
          Mode: {engineMode}
        </div>

        {engineMode === 'local' ? (
          <div className="space-y-4">
            <div className="space-y-1">
              <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">
                Step 1 — Install Ollama
              </p>
              <CopyableCommand command="brew install ollama" />
            </div>
            <div className="space-y-1">
              <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">
                Step 2 — Start the service
              </p>
              <CopyableCommand command="ollama serve" />
            </div>
            <div className="space-y-1">
              <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">
                Step 3 — Pull the model
              </p>
              <CopyableCommand command="ollama pull qwen2.5-coder:7b" />
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-gray-400">
              The remote engine at the configured URL is not reachable.
            </p>
            <div>
              <label className="text-xs font-medium text-gray-400 uppercase tracking-wide block mb-1">
                Remote URL
              </label>
              <input
                type="text"
                value={editedUrl}
                onChange={(e) => setEditedUrl(e.target.value)}
                placeholder="https://your-engine-url/..."
                className="w-full bg-gray-800 border border-white/10 rounded px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-white/30"
              />
            </div>
            <p className="text-xs text-gray-500">
              Update the URL above, then click Retry to check connectivity.
            </p>
          </div>
        )}

        <div className="mt-6 flex gap-3 justify-end">
          <button
            data-testid="engine-setup-continue-btn"
            onClick={onClose}
            className="px-4 py-2 rounded text-sm text-gray-400 hover:text-gray-200 hover:bg-white/5 transition-all"
          >
            Continue Anyway
          </button>
          <button
            data-testid="engine-setup-retry-btn"
            onClick={onRetry}
            className="px-4 py-2 rounded text-sm font-medium bg-blue-600 hover:bg-blue-500 text-white transition-all"
          >
            Retry
          </button>
        </div>
      </div>
    </div>
  );
}
