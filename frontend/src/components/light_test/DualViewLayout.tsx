import { useEffect, useRef } from 'react';
import { Eye, LayoutGrid, Lightbulb, Plus } from 'lucide-react';
import { useAppSelector } from '../../store';

function drawCrosshair(ctx: CanvasRenderingContext2D, cx: number, cy: number) {
  ctx.save();
  ctx.strokeStyle = 'rgba(255,255,255,0.15)';
  ctx.lineWidth = 1;
  ctx.setLineDash([4, 4]);
  ctx.beginPath();
  ctx.moveTo(cx - 20, cy);
  ctx.lineTo(cx + 20, cy);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(cx, cy - 20);
  ctx.lineTo(cx, cy + 20);
  ctx.stroke();
  ctx.restore();
}

export default function DualViewLayout() {
  const image = useAppSelector(s => s.light_test.image);
  const depth_result = useAppSelector(s => s.light_test.depth_result);
  const material_result = useAppSelector(s => s.light_test.material_result);
  const frontCanvasRef = useRef<HTMLCanvasElement>(null);
  const topCanvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = frontCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#1a1a1a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    drawCrosshair(ctx, canvas.width / 2, canvas.height / 2);

    if (image) {
      const img = new window.Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => {
        const scale = Math.min(
          canvas.width / (img.naturalWidth || 1),
          canvas.height / (img.naturalHeight || 1),
        );
        const w = (img.naturalWidth || canvas.width) * scale;
        const h = (img.naturalHeight || canvas.height) * scale;
        const x = (canvas.width - w) / 2;
        const y = (canvas.height - h) / 2;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, x, y, w, h);

        if (depth_result?.depth_map_base64) {
          const depthImg = new window.Image();
          depthImg.onload = () => {
            ctx.globalAlpha = 0.4;
            ctx.drawImage(depthImg, x, y, w, h);
            ctx.globalAlpha = 1;
            drawCrosshair(ctx, canvas.width / 2, canvas.height / 2);
          };
          depthImg.src = `data:image/png;base64,${depth_result.depth_map_base64}`;
        } else {
          drawCrosshair(ctx, canvas.width / 2, canvas.height / 2);
        }
      };
      img.src = `http://localhost:8000${image.file_path}`;
    }
  }, [image, depth_result]);

  useEffect(() => {
    const canvas = topCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#111111';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    drawCrosshair(ctx, canvas.width / 2, canvas.height / 2);

    if (depth_result?.depth_map_base64) {
      const depthImg = new window.Image();
      depthImg.onload = () => {
        const scale = Math.min(
          canvas.width / (depthImg.naturalWidth || 1),
          canvas.height / (depthImg.naturalHeight || 1),
        );
        const w = (depthImg.naturalWidth || canvas.width) * scale;
        const h = (depthImg.naturalHeight || canvas.height) * scale;
        const x = (canvas.width - w) / 2;
        const y = (canvas.height - h) / 2;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(depthImg, x, y, w, h);
        drawCrosshair(ctx, canvas.width / 2, canvas.height / 2);
      };
      depthImg.src = `data:image/png;base64,${depth_result.depth_map_base64}`;
    }
  }, [depth_result]);

  const hasDepth = depth_result?.depth_map_base64 != null;

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
          <canvas
            data-testid="front-view-canvas"
            ref={frontCanvasRef}
            className="w-full h-full"
            style={{ display: 'block' }}
          />
        </div>
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
          <canvas
            data-testid="top-view-canvas"
            ref={topCanvasRef}
            className="w-full h-full"
            style={{ display: 'block' }}
          />
          {!hasDepth && (
            <div
              className="absolute inset-0 flex items-center justify-center pointer-events-none"
            >
              <p className="text-xs" style={{ color: '#555555' }}>
                Depth data required
              </p>
            </div>
          )}
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
        <div className="flex-1 flex flex-col items-center justify-center gap-3 p-4">
          {material_result?.surface_type && (
            <div
              data-testid="surface-type-badge"
              className="px-2 py-1 rounded text-xs"
              style={{
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid #3a3a3a',
                color: '#a0a0a0',
              }}
            >
              {material_result.surface_type}
            </div>
          )}
          <p className="text-xs text-center" style={{ color: '#555555' }}>
            Controls will appear here
          </p>
          <button
            data-testid="add-light-btn"
            className="flex items-center gap-2 px-3 py-1.5 rounded text-xs transition-all duration-150"
            style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid #2a2a2a',
              color: '#a0a0a0',
            }}
          >
            <Plus size={12} />
            Add Light
          </button>
        </div>
      </div>
    </div>
  );
}
