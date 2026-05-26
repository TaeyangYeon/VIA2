import { Lightbulb } from 'lucide-react';

interface Props {
  suggestions: string[];
}

export default function LightingSuggestion({ suggestions }: Props) {
  const handleOpenLightTest = () => {
    window.alert('Navigate to Light Test');
  };

  return (
    <div
      data-testid="lighting-suggestion-list"
      className="bg-white/5 backdrop-blur border border-white/10 rounded-lg overflow-hidden"
    >
      <div className="px-4 py-3 border-b border-white/10 flex items-center gap-2">
        <Lightbulb size={14} className="text-text-secondary" />
        <p className="text-xs font-medium text-text-secondary uppercase tracking-wider">
          Lighting Suggestions
        </p>
      </div>

      <div className="p-3 flex flex-col gap-2">
        {suggestions.map((suggestion, index) => (
          <div
            key={index}
            data-testid={`lighting-card-${index}`}
            className="border border-white/8 rounded p-3 text-sm text-text-secondary"
            style={{ background: 'rgba(255,255,255,0.03)' }}
          >
            {suggestion}
          </div>
        ))}
      </div>

      <div className="px-4 py-3 border-t border-white/10">
        <button
          data-testid="open-light-test-btn"
          onClick={handleOpenLightTest}
          className="flex items-center gap-2 px-3 py-1.5 rounded bg-white/5 border border-white/10 text-xs text-text-secondary hover:bg-white/10 hover:text-text-primary transition-all duration-150"
        >
          <Lightbulb size={12} />
          <span>Open Light Test</span>
        </button>
      </div>
    </div>
  );
}
