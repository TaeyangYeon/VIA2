import { useRef, useEffect, useState, useCallback } from 'react';
import {
  Crosshair,
  Trash2,
  Save,
  AlertCircle,
  Loader2,
  Image as ImageIcon,
} from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../store';
import { setRoi as setRoiStore, clearRoi as clearRoiStore } from '../store/slices/roiSlice';
import { setRoi as apiSetRoi, clearRoi as apiClearRoi } from '../services/api';
import type { ROICoordinates } from '../services/types';
import { useROIDrawing, type DrawContext } from '../hooks/useROIDrawing';

const BASE_URL = 'http://localhost:8000';

type LoadState = 'idle' | 'loading' | 'loaded' | 'error';

export default function ROICanvas() {
  const dispatch = useAppDispatch();
  const analysisImages = useAppSelector(state => state.images.analysis);
  const storedRoi = useAppSelector(state => state.roi);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);

  const [loadState, setLoadState] = useState<LoadState>('idle');
  const [imgDim, setImgDim] = useState({ width: 0, height: 0 });
  const [localRoi, setLocalRoi] = useState<ROICoordinates | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const { isDrawing, roi: drawnRoi, startDraw, updateDraw, endDraw, clearROI: clearDrawing } =
    useROIDrawing();

  const firstImage = analysisImages[0] ?? null;
  const imageUrl = firstImage ? `${BASE_URL}/api/images/${firstImage.id}/file` : null;

  // Initialize localRoi from store
  useEffect(() => {
    setLocalRoi(storedRoi);
  }, [storedRoi]);

  // Sync drawn roi into localRoi when drawing ends
  useEffect(() => {
    if (!isDrawing && drawnRoi !== null) {
      setLocalRoi(drawnRoi);
    }
  }, [isDrawing, drawnRoi]);

  // Load image whenever imageUrl changes
  useEffect(() => {
    if (!imageUrl) {
      setLoadState('idle');
      imageRef.current = null;
      return;
    }
    setLoadState('loading');
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      imageRef.current = img;
      setImgDim({ width: img.naturalWidth, height: img.naturalHeight });
      setLoadState('loaded');
    };
    img.onerror = () => setLoadState('error');
    img.src = imageUrl;
    return () => {
      img.onload = null;
      img.onerror = null;
    };
  }, [imageUrl]);

  // Resize canvas to container on load
  useEffect(() => {
    if (loadState !== 'loaded') return;
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;
    const { clientWidth, clientHeight } = container;
    if (clientWidth > 0) canvas.width = clientWidth;
    if (clientHeight > 0) canvas.height = clientHeight;
  }, [loadState]);

  // Draw image + ROI overlay onto canvas
  const drawCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    const img = imageRef.current;
    if (!canvas || !img || loadState !== 'loaded') return;

    const ctx2d = canvas.getContext('2d');
    if (!ctx2d) return;

    const W = canvas.width;
    const H = canvas.height;
    if (W === 0 || H === 0 || imgDim.width === 0 || imgDim.height === 0) return;

    const scale = Math.min(W / imgDim.width, H / imgDim.height);
    const displayW = imgDim.width * scale;
    const displayH = imgDim.height * scale;
    const offsetX = (W - displayW) / 2;
    const offsetY = (H - displayH) / 2;

    ctx2d.clearRect(0, 0, W, H);
    ctx2d.drawImage(img, offsetX, offsetY, displayW, displayH);

    const currentRoi = isDrawing ? drawnRoi : localRoi;
    if (currentRoi) {
      const rx = currentRoi.x1 * scale + offsetX;
      const ry = currentRoi.y1 * scale + offsetY;
      const rw = (currentRoi.x2 - currentRoi.x1) * scale;
      const rh = (currentRoi.y2 - currentRoi.y1) * scale;

      // Dark overlay over entire image region
      ctx2d.fillStyle = 'rgba(0, 0, 0, 0.45)';
      ctx2d.fillRect(offsetX, offsetY, displayW, displayH);

      // Redraw the ROI region at full brightness
      ctx2d.drawImage(
        img,
        currentRoi.x1,
        currentRoi.y1,
        currentRoi.x2 - currentRoi.x1,
        currentRoi.y2 - currentRoi.y1,
        rx,
        ry,
        rw,
        rh,
      );

      // ROI border
      ctx2d.strokeStyle = 'rgba(255, 255, 255, 0.9)';
      ctx2d.lineWidth = 1.5;
      ctx2d.setLineDash([6, 3]);
      ctx2d.strokeRect(rx, ry, rw, rh);
      ctx2d.setLineDash([]);

      // Corner handles
      ctx2d.fillStyle = 'rgba(255, 255, 255, 0.9)';
      const hs = 6;
      [
        [rx, ry],
        [rx + rw, ry],
        [rx, ry + rh],
        [rx + rw, ry + rh],
      ].forEach(([hx, hy]) => {
        ctx2d.fillRect(hx - hs / 2, hy - hs / 2, hs, hs);
      });
    }
  }, [loadState, isDrawing, drawnRoi, localRoi, imgDim]);

  useEffect(() => {
    drawCanvas();
  }, [drawCanvas]);

  // Mouse event helpers
  const getDrawContext = (): DrawContext | null => {
    const canvas = canvasRef.current;
    if (!canvas || imgDim.width === 0) return null;
    return {
      canvasWidth: canvas.width,
      canvasHeight: canvas.height,
      imageWidth: imgDim.width,
      imageHeight: imgDim.height,
    };
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = getDrawContext();
    if (!ctx) return;
    const rect = canvas.getBoundingClientRect();
    startDraw(e.clientX - rect.left, e.clientY - rect.top, ctx);
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = getDrawContext();
    if (!ctx) return;
    const rect = canvas.getBoundingClientRect();
    updateDraw(e.clientX - rect.left, e.clientY - rect.top, ctx);
  };

  const handleMouseUp = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = getDrawContext();
    if (!ctx) return;
    const rect = canvas.getBoundingClientRect();
    endDraw(e.clientX - rect.left, e.clientY - rect.top, ctx);
  };

  const handleSave = async () => {
    if (!localRoi) return;
    setIsSaving(true);
    setSaveError(null);
    try {
      await apiSetRoi(localRoi);
      dispatch(setRoiStore(localRoi));
    } catch {
      setSaveError('Failed to save ROI');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    clearDrawing();
    setLocalRoi(null);
    dispatch(clearRoiStore());
    try {
      await apiClearRoi();
    } catch {
      // best-effort
    }
  };

  const handleCoordChange = (field: keyof ROICoordinates, value: string) => {
    const num = parseInt(value, 10);
    if (isNaN(num)) return;
    setLocalRoi(prev =>
      prev ? { ...prev, [field]: num } : { x1: 0, y1: 0, x2: 0, y2: 0, [field]: num },
    );
  };

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div
      data-testid="roi-panel"
      className="flex flex-col h-full p-4 gap-3 overflow-hidden bg-bg-top"
    >
      {/* Header */}
      <div className="flex items-center gap-2 flex-shrink-0">
        <Crosshair size={16} className="text-text-secondary" />
        <h2 className="text-sm font-semibold text-text-primary">ROI Drawing</h2>
        {firstImage && (
          <span className="text-xs text-text-disabled ml-auto truncate max-w-[200px]">
            {firstImage.original_filename}
          </span>
        )}
      </div>

      {/* Canvas area */}
      <div
        ref={containerRef}
        className="flex-1 relative rounded border border-white/10 bg-white/5 overflow-hidden min-h-0"
      >
        {/* Empty state */}
        {loadState === 'idle' && (
          <div
            data-testid="roi-empty-state"
            className="absolute inset-0 flex flex-col items-center justify-center gap-3 text-center"
          >
            <ImageIcon size={36} className="text-text-disabled" />
            <p className="text-sm text-text-secondary">
              Upload images first to draw an ROI
            </p>
            <p className="text-xs text-text-disabled">
              Go to the Input panel and upload analysis images
            </p>
          </div>
        )}

        {/* Loading state */}
        {loadState === 'loading' && (
          <div
            data-testid="roi-loading"
            className="absolute inset-0 flex flex-col items-center justify-center gap-2"
          >
            <Loader2 size={28} className="text-text-secondary animate-spin" />
            <p className="text-xs text-text-disabled">Loading image…</p>
          </div>
        )}

        {/* Error state */}
        {loadState === 'error' && (
          <div
            data-testid="roi-error"
            className="absolute inset-0 flex flex-col items-center justify-center gap-3"
          >
            <AlertCircle size={32} className="text-accent-error" />
            <p className="text-sm text-text-secondary">Failed to load image</p>
            <p className="text-xs text-text-disabled">
              Check that the backend is running and the image file exists
            </p>
          </div>
        )}

        {/* Canvas */}
        {loadState === 'loaded' && (
          <canvas
            ref={canvasRef}
            data-testid="roi-canvas"
            width={800}
            height={500}
            className="absolute inset-0 w-full h-full"
            style={{ cursor: isDrawing ? 'crosshair' : 'crosshair' }}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          />
        )}
      </div>

      {/* Controls */}
      <div className="flex-shrink-0 flex flex-col gap-2">
        {/* Coordinate inputs */}
        {localRoi && (
          <div
            data-testid="roi-coords-panel"
            className="rounded border border-white/10 bg-white/5 backdrop-blur p-3 grid grid-cols-2 gap-2"
          >
            {(
              [
                { field: 'x1', label: 'X1' },
                { field: 'y1', label: 'Y1' },
                { field: 'x2', label: 'X2' },
                { field: 'y2', label: 'Y2' },
              ] as { field: keyof ROICoordinates; label: string }[]
            ).map(({ field, label }) => (
              <label key={field} className="flex items-center gap-1.5">
                <span className="text-xs text-text-disabled w-5 shrink-0">{label}</span>
                <input
                  data-testid={`roi-${field}-input`}
                  type="number"
                  min={0}
                  value={localRoi[field]}
                  onChange={e => handleCoordChange(field, e.target.value)}
                  disabled={isDrawing}
                  className="
                    flex-1 min-w-0 bg-white/5 border border-white/10 rounded px-2 py-1
                    text-xs text-text-primary text-right font-mono
                    focus:outline-none focus:border-white/30
                    disabled:opacity-50 disabled:cursor-not-allowed
                    transition-all duration-150
                  "
                />
              </label>
            ))}
          </div>
        )}

        {/* Hint when no ROI */}
        {!localRoi && loadState === 'loaded' && (
          <p className="text-xs text-text-disabled text-center">
            Drag on the image to draw an ROI
          </p>
        )}

        {/* Action buttons */}
        {loadState === 'loaded' && (
          <div className="flex gap-2">
            <button
              data-testid="roi-delete-btn"
              onClick={handleDelete}
              disabled={!localRoi || isSaving}
              className="
                flex items-center gap-1.5 px-3 py-1.5 rounded border border-white/10
                bg-white/5 text-xs text-text-secondary
                hover:bg-white/8 hover:text-text-primary
                disabled:opacity-40 disabled:cursor-not-allowed
                transition-all duration-150
              "
            >
              <Trash2 size={13} />
              Delete
            </button>

            <button
              data-testid="roi-save-btn"
              onClick={handleSave}
              disabled={!localRoi || isSaving}
              className="
                flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded border border-white/10
                bg-white/8 text-xs text-text-primary
                hover:bg-white/12
                disabled:opacity-40 disabled:cursor-not-allowed
                transition-all duration-150
              "
            >
              {isSaving ? (
                <Loader2 size={13} className="animate-spin" />
              ) : (
                <Save size={13} />
              )}
              {isSaving ? 'Saving…' : 'Save ROI'}
            </button>
          </div>
        )}

        {/* Save error */}
        {saveError && (
          <p className="text-xs text-accent-error flex items-center gap-1">
            <AlertCircle size={11} />
            {saveError}
          </p>
        )}
      </div>
    </div>
  );
}
