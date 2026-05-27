import { useEffect, useRef } from 'react';
import { useAppSelector } from '../../store';

const CHANNEL_COLORS: Record<string, string> = {
  R: '#f87171',
  G: '#4ade80',
  B: '#60a5fa',
  L: '#a0a0a0',
};

interface ChannelData {
  name: string;
  bins: number[];
}

function computeHistogramFromPixels(imageData: ImageData): ChannelData[] {
  const { data, width, height } = imageData;
  const rBins = new Array<number>(256).fill(0);
  const gBins = new Array<number>(256).fill(0);
  const bBins = new Array<number>(256).fill(0);

  for (let i = 0; i < width * height * 4; i += 4) {
    rBins[data[i]]++;
    gBins[data[i + 1]]++;
    bBins[data[i + 2]]++;
  }

  return [
    { name: 'R', bins: rBins },
    { name: 'G', bins: gBins },
    { name: 'B', bins: bBins },
  ];
}

function drawHistogram(
  canvas: HTMLCanvasElement,
  channels: ChannelData[],
  isGrayscale: boolean,
): void {
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const W = canvas.width;
  const H = canvas.height;
  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = '#0a0a0a';
  ctx.fillRect(0, 0, W, H);

  const channelsToRender = isGrayscale
    ? [{ name: 'L', bins: channels[0]?.bins ?? [] }]
    : channels;

  const allBins = channelsToRender.flatMap(c => c.bins);
  const maxVal = Math.max(...allBins, 1);

  for (const ch of channelsToRender) {
    const color = CHANNEL_COLORS[ch.name] ?? '#a0a0a0';
    ctx.globalAlpha = 0.6;
    ctx.strokeStyle = color;
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let i = 0; i < 256; i++) {
      const x = (i / 256) * W;
      const y = H - (ch.bins[i] / maxVal) * H;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }
  ctx.globalAlpha = 1;
}

export default function HistogramPanel() {
  const rendered_result = useAppSelector(s => s.light_test.rendered_result);
  const is_grayscale = useAppSelector(s => s.light_test.is_grayscale);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const histCanvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!rendered_result) return;
    const canvas = canvasRef.current;
    const histCanvas = histCanvasRef.current;
    if (!canvas || !histCanvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new window.Image();
    img.onload = () => {
      canvas.width = img.naturalWidth || 1;
      canvas.height = img.naturalHeight || 1;
      ctx.drawImage(img, 0, 0);

      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const channels = computeHistogramFromPixels(imageData);
      drawHistogram(histCanvas, channels, is_grayscale);
    };
    img.src = `data:image/png;base64,${rendered_result}`;
  }, [rendered_result, is_grayscale]);

  return (
    <div
      data-testid="histogram-panel"
      style={{
        padding: '8px 12px',
        borderTop: '1px solid #1a1a1a',
        display: 'flex',
        flexDirection: 'column',
        gap: 4,
      }}
    >
      <p
        style={{
          color: '#555555',
          fontSize: '0.65rem',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          marginBottom: 2,
        }}
      >
        Histogram
      </p>

      {/* Hidden canvas for pixel sampling */}
      <canvas ref={canvasRef} style={{ display: 'none' }} />

      <canvas
        data-testid="histogram-canvas"
        ref={histCanvasRef}
        width={220}
        height={60}
        style={{
          width: '100%',
          height: 60,
          borderRadius: 4,
          border: '1px solid #1a1a1a',
          background: '#0a0a0a',
        }}
      />

      {!rendered_result && (
        <p style={{ color: '#3a3a3a', fontSize: '0.7rem' }}>No render yet</p>
      )}

      {rendered_result && (
        <div style={{ display: 'flex', gap: 8 }}>
          {is_grayscale ? (
            <span data-testid="histogram-channel-l" style={{ color: '#a0a0a0', fontSize: '0.65rem' }}>
              L
            </span>
          ) : (
            <>
              <span data-testid="histogram-channel-r" style={{ color: '#f87171', fontSize: '0.65rem' }}>R</span>
              <span data-testid="histogram-channel-g" style={{ color: '#4ade80', fontSize: '0.65rem' }}>G</span>
              <span data-testid="histogram-channel-b" style={{ color: '#60a5fa', fontSize: '0.65rem' }}>B</span>
            </>
          )}
        </div>
      )}
    </div>
  );
}
