import { useState } from 'react';
import {
  Image as ImageIcon,
  Crop,
  Cpu,
  FileText,
  Settings,
  Play,
  BarChart2,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import InputPanel from './panels/InputPanel';
import ROICanvas from './ROICanvas';

type PanelId = 'input' | 'roi' | 'engine' | 'directive' | 'config' | 'execution' | 'result';

interface NavItem {
  id: PanelId;
  label: string;
  icon: React.ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  { id: 'input',     label: 'Input',     icon: <ImageIcon  size={18} /> },
  { id: 'roi',       label: 'ROI',       icon: <Crop       size={18} /> },
  { id: 'engine',    label: 'Engine',    icon: <Cpu        size={18} /> },
  { id: 'directive', label: 'Directive', icon: <FileText   size={18} /> },
  { id: 'config',    label: 'Config',    icon: <Settings   size={18} /> },
  { id: 'execution', label: 'Execution', icon: <Play       size={18} /> },
  { id: 'result',    label: 'Result',    icon: <BarChart2  size={18} /> },
];

function PlaceholderPanel({ label }: { label: string }) {
  return (
    <div className="flex items-center justify-center h-full">
      <p className="text-text-disabled text-sm">{label} panel — coming soon</p>
    </div>
  );
}

function ActivePanel({ id }: { id: PanelId }) {
  switch (id) {
    case 'input':     return <InputPanel />;
    case 'roi':       return <ROICanvas />;
    case 'engine':    return <PlaceholderPanel label="Engine" />;
    case 'directive': return <PlaceholderPanel label="Directive" />;
    case 'config':    return <PlaceholderPanel label="Config" />;
    case 'execution': return <PlaceholderPanel label="Execution" />;
    case 'result':    return <PlaceholderPanel label="Result" />;
  }
}

export default function Layout() {
  const [activePanel, setActivePanel] = useState<PanelId>('input');
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-bg-top">
      {/* Sidebar */}
      <aside
        data-testid="sidebar"
        data-collapsed={collapsed}
        className={`
          relative flex flex-col glass-panel flex-shrink-0 transition-all duration-200
          ${collapsed ? 'w-14' : 'w-[280px]'}
        `}
      >
        {/* Logo / Title */}
        <div className="flex items-center gap-3 px-4 py-4 border-b border-border-default flex-shrink-0">
          <div className="w-6 h-6 rounded bg-white/10 flex items-center justify-center flex-shrink-0">
            <span className="text-[10px] font-bold text-text-primary font-mono">V2</span>
          </div>
          {!collapsed && (
            <span className="text-sm font-semibold text-text-primary tracking-wide whitespace-nowrap overflow-hidden">
              VIA2
            </span>
          )}
        </div>

        {/* Nav items */}
        <nav className="flex-1 overflow-y-auto py-2">
          {NAV_ITEMS.map(item => (
            <button
              key={item.id}
              data-testid={`nav-${item.id}`}
              data-active={activePanel === item.id}
              onClick={() => setActivePanel(item.id)}
              className={`
                w-full flex items-center gap-3 px-4 py-2.5 text-left
                transition-all duration-150 relative
                ${activePanel === item.id
                  ? 'bg-white/8 text-text-primary'
                  : 'text-text-secondary hover:bg-white/5 hover:text-text-primary'
                }
              `}
            >
              {/* Active indicator */}
              {activePanel === item.id && (
                <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-accent-action rounded-r" />
              )}
              <span className="flex-shrink-0">{item.icon}</span>
              <span
                className="text-sm font-medium whitespace-nowrap overflow-hidden transition-all duration-200"
                style={collapsed ? { display: 'none' } : undefined}
              >
                {item.label}
              </span>
            </button>
          ))}
        </nav>

        {/* Collapse toggle */}
        <div className="flex-shrink-0 border-t border-border-default p-2">
          <button
            data-testid="sidebar-toggle"
            onClick={() => setCollapsed(c => !c)}
            className="w-full flex items-center justify-center h-8 rounded hover:bg-white/5 text-text-disabled hover:text-text-secondary transition-all duration-150"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>
      </aside>

      {/* Main workspace */}
      <main
        data-testid="main-workspace"
        className="flex-1 overflow-hidden bg-bg-top"
      >
        <ActivePanel id={activePanel} />
      </main>
    </div>
  );
}
