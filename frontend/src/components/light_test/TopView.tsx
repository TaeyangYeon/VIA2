import { useEffect, useRef } from 'react';
import { Camera } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../../store';
import { selectLight } from '../../store/slices/lightTestSlice';
import type { TopViewLight } from '../../hooks/useLightSync';

interface TopViewProps {
  topViewLights: TopViewLight[];
  onDrag: (lightId: string, deltaX: number, deltaZ: number) => void;
}

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

function TopLightShape({ shape, selected }: { shape: TopViewLight['shape']; selected: boolean }) {
  const color = selected ? '#ffffff' : '#a0a0a0';
  const size = 16;
  switch (shape) {
    case 'ring':
    case 'dome':
    case 'low_angle_ring':
      return (
        <div
          style={{
            width: size,
            height: size,
            borderRadius: '50%',
            border: `2px solid ${color}`,
          }}
        />
      );
    case 'bar':
      return (
        <div
          style={{
            width: size * 1.8,
            height: size * 0.5,
            border: `2px solid ${color}`,
            borderRadius: 2,
          }}
        />
      );
    case 'spot':
    case 'coaxial':
      return (
        <div
          style={{
            width: size * 0.6,
            height: size * 0.6,
            borderRadius: '50%',
            background: color,
          }}
        />
      );
    default:
      return (
        <div
          style={{
            width: size,
            height: size,
            borderRadius: '50%',
            border: `2px solid ${color}`,
          }}
        />
      );
  }
}

export default function TopView({ topViewLights, onDrag }: TopViewProps) {
  const dispatch = useAppDispatch();
  const depth_result = useAppSelector(s => s.light_test.depth_result);
  const selected_light_id = useAppSelector(s => s.light_test.selected_light_id);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const dragRef = useRef<{ lightId: string; startX: number; startY: number } | null>(null);
  const hasDepth = depth_result?.depth_map_base64 != null;

  useEffect(() => {
    const canvas = canvasRef.current;
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

  const handleMouseDown = (lightId: string, e: React.MouseEvent) => {
    e.preventDefault();
    dragRef.current = { lightId, startX: e.clientX, startY: e.clientY };
    dispatch(selectLight(lightId));

    const handleMouseMove = (ev: MouseEvent) => {
      if (!dragRef.current) return;
      const dx = ev.clientX - dragRef.current.startX;
      const dz = ev.clientY - dragRef.current.startY;
      dragRef.current.startX = ev.clientX;
      dragRef.current.startY = ev.clientY;
      onDrag(lightId, dx, dz);
    };

    const handleMouseUp = () => {
      dragRef.current = null;
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
  };

  return (
    <div
      data-testid="top-view-container"
      style={{ position: 'relative', flex: 1, overflow: 'hidden', width: '100%', height: '100%' }}
    >
      <canvas
        data-testid="top-view-canvas"
        ref={canvasRef}
        style={{ display: 'block', width: '100%', height: '100%' }}
      />

      {!hasDepth && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            pointerEvents: 'none',
          }}
        >
          <p style={{ color: '#555555', fontSize: '0.75rem' }}>Depth data required</p>
        </div>
      )}

      {/* Camera marker fixed at center */}
      <div
        data-testid="top-camera-marker"
        style={{
          position: 'absolute',
          bottom: '8%',
          left: '50%',
          transform: 'translateX(-50%)',
          color: '#a0a0a0',
          pointerEvents: 'none',
        }}
      >
        <Camera size={16} />
      </div>

      {/* Light icons */}
      {topViewLights.map(light => {
        const isSelected = light.id === selected_light_id;
        return (
          <div
            key={light.id}
            data-testid={`top-light-${light.id}`}
            style={{
              position: 'absolute',
              left: `${light.screenX * 100}%`,
              top: `${light.screenZ * 100}%`,
              transform: 'translate(-50%, -50%)',
              cursor: 'grab',
              border: isSelected ? '2px solid #ffffff' : '1px solid transparent',
              borderRadius: 4,
              padding: 4,
              userSelect: 'none',
              transition: 'border-color 150ms ease-in-out',
            }}
            onMouseDown={(e) => handleMouseDown(light.id, e)}
          >
            <TopLightShape shape={light.shape} selected={isSelected} />
          </div>
        );
      })}
    </div>
  );
}
