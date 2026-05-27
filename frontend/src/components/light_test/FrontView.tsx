import { useEffect, useRef } from 'react';
import { useAppDispatch, useAppSelector } from '../../store';
import { selectLight } from '../../store/slices/lightTestSlice';
import type { FrontViewLight } from '../../hooks/useLightSync';

interface FrontViewProps {
  frontViewLights: FrontViewLight[];
  onDrag: (lightId: string, deltaX: number, deltaY: number) => void;
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

function LightShape({ shape, selected }: { shape: FrontViewLight['shape']; selected: boolean }) {
  const color = selected ? '#ffffff' : '#a0a0a0';
  const size = 20;
  switch (shape) {
    case 'ring':
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
      return (
        <div
          style={{
            width: 0,
            height: 0,
            borderLeft: `${size / 2}px solid transparent`,
            borderRight: `${size / 2}px solid transparent`,
            borderTop: `${size}px solid ${color}`,
          }}
        />
      );
    case 'coaxial':
      return (
        <div
          style={{
            width: size,
            height: size,
            borderRadius: '50%',
            background: color,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <div style={{ width: 2, height: size, background: '#000', position: 'absolute' }} />
          <div style={{ width: size, height: 2, background: '#000', position: 'absolute' }} />
        </div>
      );
    case 'dome':
      return (
        <div
          style={{
            width: size,
            height: size / 2,
            borderRadius: `${size}px ${size}px 0 0`,
            border: `2px solid ${color}`,
            borderBottom: 'none',
          }}
        />
      );
    case 'low_angle_ring':
      return (
        <div
          style={{
            width: size * 1.5,
            height: size * 0.4,
            borderRadius: '50%',
            border: `2px solid ${color}`,
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

export default function FrontView({ frontViewLights, onDrag }: FrontViewProps) {
  const dispatch = useAppDispatch();
  const image = useAppSelector(s => s.light_test.image);
  const depth_result = useAppSelector(s => s.light_test.depth_result);
  const selected_light_id = useAppSelector(s => s.light_test.selected_light_id);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const dragRef = useRef<{ lightId: string; startX: number; startY: number } | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
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

  const handleMouseDown = (lightId: string, e: React.MouseEvent) => {
    e.preventDefault();
    dragRef.current = { lightId, startX: e.clientX, startY: e.clientY };
    dispatch(selectLight(lightId));

    const handleMouseMove = (ev: MouseEvent) => {
      if (!dragRef.current) return;
      const dx = ev.clientX - dragRef.current.startX;
      const dy = ev.clientY - dragRef.current.startY;
      dragRef.current.startX = ev.clientX;
      dragRef.current.startY = ev.clientY;
      onDrag(lightId, dx, dy);
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
      data-testid="front-view-container"
      style={{ position: 'relative', flex: 1, overflow: 'hidden', width: '100%', height: '100%' }}
    >
      <canvas
        data-testid="front-view-canvas"
        ref={canvasRef}
        style={{ display: 'block', width: '100%', height: '100%' }}
      />
      {frontViewLights.map(light => {
        const isSelected = light.id === selected_light_id;
        return (
          <div
            key={light.id}
            data-testid={`front-light-${light.id}`}
            style={{
              position: 'absolute',
              left: `${light.screenX * 100}%`,
              top: `${light.screenY * 100}%`,
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
            {isSelected && (
              <div
                data-testid="front-light-selected"
                style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}
              />
            )}
            <LightShape shape={light.shape} selected={isSelected} />
          </div>
        );
      })}
    </div>
  );
}
