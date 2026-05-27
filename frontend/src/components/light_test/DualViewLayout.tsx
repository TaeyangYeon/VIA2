import { Eye, LayoutGrid, Lightbulb } from 'lucide-react';
import { useLightSync } from '../../hooks/useLightSync';
import FrontView from './FrontView';
import TopView from './TopView';
import LightController from './LightController';
import RenderEngine from './RenderEngine';
import ColorLightControl from './ColorLightControl';
import PolarizerControl from './PolarizerControl';
import HistogramPanel from './HistogramPanel';

export default function DualViewLayout() {
  const { frontViewLights, topViewLights, handleFrontDrag, handleTopDrag } = useLightSync();

  return (
    <div
      data-testid="dual-view-layout"
      className="flex h-full"
      style={{ background: '#0a0a0a' }}
    >
      {/* Front View */}
      <div
        data-testid="front-view-panel"
        className="flex flex-col"
        style={{ flex: '0 0 45%', borderRight: '1px solid #2a2a2a' }}
      >
        <div
          className="flex items-center gap-2 px-3 py-2 flex-shrink-0"
          style={{ borderBottom: '1px solid #2a2a2a' }}
        >
          <Eye size={14} style={{ color: '#a0a0a0' }} />
          <span className="text-xs font-medium" style={{ color: '#a0a0a0' }}>
            Front View (정면도)
          </span>
        </div>
        <div className="flex-1 relative overflow-hidden">
          <FrontView frontViewLights={frontViewLights} onDrag={handleFrontDrag} />
          <RenderEngine />
        </div>
        <HistogramPanel />
      </div>

      {/* Top View */}
      <div
        data-testid="top-view-panel"
        className="flex flex-col"
        style={{ flex: '0 0 45%', borderRight: '1px solid #2a2a2a' }}
      >
        <div
          className="flex items-center gap-2 px-3 py-2 flex-shrink-0"
          style={{ borderBottom: '1px solid #2a2a2a' }}
        >
          <LayoutGrid size={14} style={{ color: '#a0a0a0' }} />
          <span className="text-xs font-medium" style={{ color: '#a0a0a0' }}>
            Top View (평면도)
          </span>
        </div>
        <div className="flex-1 relative overflow-hidden">
          <TopView topViewLights={topViewLights} onDrag={handleTopDrag} />
        </div>
      </div>

      {/* Light Controls */}
      <div
        data-testid="light-controls-panel"
        className="flex flex-col flex-1"
        style={{ minWidth: '160px' }}
      >
        <div
          className="flex items-center gap-2 px-3 py-2 flex-shrink-0"
          style={{ borderBottom: '1px solid #2a2a2a' }}
        >
          <Lightbulb size={14} style={{ color: '#a0a0a0' }} />
          <span className="text-xs font-medium" style={{ color: '#a0a0a0' }}>
            Light Controls
          </span>
        </div>
        <div className="flex-1 overflow-y-auto">
          <LightController />
          <ColorLightControl />
          <PolarizerControl />
        </div>
      </div>
    </div>
  );
}
