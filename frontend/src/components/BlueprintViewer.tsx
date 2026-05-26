import { useState, useRef, useCallback } from 'react';
import { ZoomIn, ZoomOut, RotateCcw, Maximize2 } from 'lucide-react';

interface Props {
  svgContent: string;
  onNodeClick?: (nodeId: string) => void;
}

const MIN_SCALE = 0.25;
const MAX_SCALE = 4;
const SCALE_STEP = 0.25;

export default function BlueprintViewer({ svgContent, onNodeClick }: Props) {
  const [scale, setScale] = useState(1);
  const [translateX, setTranslateX] = useState(0);
  const [translateY, setTranslateY] = useState(0);
  const isDragging = useRef(false);
  const dragStart = useRef({ x: 0, y: 0 });

  const zoomIn = () => setScale(s => Math.min(MAX_SCALE, +(s + SCALE_STEP).toFixed(2)));
  const zoomOut = () => setScale(s => Math.max(MIN_SCALE, +(s - SCALE_STEP).toFixed(2)));
  const resetView = () => {
    setScale(1);
    setTranslateX(0);
    setTranslateY(0);
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    isDragging.current = true;
    dragStart.current = { x: e.clientX - translateX, y: e.clientY - translateY };
  };

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (!isDragging.current) return;
      setTranslateX(e.clientX - dragStart.current.x);
      setTranslateY(e.clientY - dragStart.current.y);
    },
    []
  );

  const handleMouseUp = () => {
    isDragging.current = false;
  };

  const handleClick = (e: React.MouseEvent) => {
    const target = e.target as Element;
    const nodeEl = target.closest('[data-node-id]');
    if (nodeEl) {
      const nodeId = nodeEl.getAttribute('data-node-id');
      if (nodeId && onNodeClick) onNodeClick(nodeId);
    }
  };

  return (
    <div
      data-testid="blueprint-viewer"
      className="bg-white/5 backdrop-blur border border-white/10 rounded-lg flex flex-col overflow-hidden"
      style={{ minHeight: '300px' }}
    >
      {/* Controls toolbar */}
      <div className="flex items-center gap-1 px-3 py-2 border-b border-white/10 flex-shrink-0">
        <button
          data-testid="zoom-in-btn"
          onClick={zoomIn}
          className="w-7 h-7 flex items-center justify-center rounded hover:bg-white/10 text-text-secondary hover:text-text-primary transition-all duration-150"
          title="Zoom in"
        >
          <ZoomIn size={14} />
        </button>
        <button
          data-testid="zoom-out-btn"
          onClick={zoomOut}
          className="w-7 h-7 flex items-center justify-center rounded hover:bg-white/10 text-text-secondary hover:text-text-primary transition-all duration-150"
          title="Zoom out"
        >
          <ZoomOut size={14} />
        </button>
        <span
          data-testid="scale-display"
          className="text-xs text-text-disabled w-10 text-center select-none"
        >
          {Math.round(scale * 100)}%
        </span>
        <div className="w-px h-4 bg-white/10 mx-1 flex-shrink-0" />
        <button
          data-testid="reset-btn"
          onClick={resetView}
          className="w-7 h-7 flex items-center justify-center rounded hover:bg-white/10 text-text-secondary hover:text-text-primary transition-all duration-150"
          title="Reset view"
        >
          <RotateCcw size={14} />
        </button>
        <button
          data-testid="fit-btn"
          onClick={resetView}
          className="w-7 h-7 flex items-center justify-center rounded hover:bg-white/10 text-text-secondary hover:text-text-primary transition-all duration-150"
          title="Fit to container"
        >
          <Maximize2 size={14} />
        </button>
      </div>

      {/* SVG canvas */}
      <div
        className="flex-1 overflow-hidden cursor-grab"
        style={{ minHeight: '200px' }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onClick={handleClick}
      >
        <div
          data-testid="svg-transform-container"
          style={{
            transform: `translate(${translateX}px, ${translateY}px) scale(${scale})`,
            transformOrigin: '0 0',
            display: 'inline-block',
          }}
          dangerouslySetInnerHTML={{ __html: svgContent }}
        />
      </div>
    </div>
  );
}
