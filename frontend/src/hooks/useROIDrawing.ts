import { useState, useCallback, useRef } from 'react';
import type { ROICoordinates } from '../services/types';

export interface DrawContext {
  canvasWidth: number;
  canvasHeight: number;
  imageWidth: number;
  imageHeight: number;
}

export interface UseROIDrawingReturn {
  isDrawing: boolean;
  roi: ROICoordinates | null;
  startDraw: (x: number, y: number, ctx: DrawContext) => void;
  updateDraw: (x: number, y: number, ctx: DrawContext) => void;
  endDraw: (x: number, y: number, ctx: DrawContext) => void;
  clearROI: () => void;
}

function canvasToImage(x: number, y: number, ctx: DrawContext): { ix: number; iy: number } {
  const scale = Math.min(ctx.canvasWidth / ctx.imageWidth, ctx.canvasHeight / ctx.imageHeight);
  const offsetX = (ctx.canvasWidth - ctx.imageWidth * scale) / 2;
  const offsetY = (ctx.canvasHeight - ctx.imageHeight * scale) / 2;
  const ix = Math.round(Math.max(0, Math.min(ctx.imageWidth, (x - offsetX) / scale)));
  const iy = Math.round(Math.max(0, Math.min(ctx.imageHeight, (y - offsetY) / scale)));
  return { ix, iy };
}

export function useROIDrawing(): UseROIDrawingReturn {
  const [isDrawing, setIsDrawing] = useState(false);
  const [roi, setRoi] = useState<ROICoordinates | null>(null);
  const startRef = useRef<{ x: number; y: number } | null>(null);

  const startDraw = useCallback((x: number, y: number, ctx: DrawContext) => {
    const { ix, iy } = canvasToImage(x, y, ctx);
    startRef.current = { x: ix, y: iy };
    setIsDrawing(true);
    setRoi({ x1: ix, y1: iy, x2: ix, y2: iy });
  }, []);

  const updateDraw = useCallback((x: number, y: number, ctx: DrawContext) => {
    if (!startRef.current) return;
    const { ix, iy } = canvasToImage(x, y, ctx);
    const sp = startRef.current;
    setRoi({
      x1: Math.min(sp.x, ix),
      y1: Math.min(sp.y, iy),
      x2: Math.max(sp.x, ix),
      y2: Math.max(sp.y, iy),
    });
  }, []);

  const endDraw = useCallback((x: number, y: number, ctx: DrawContext) => {
    if (!startRef.current) return;
    const { ix, iy } = canvasToImage(x, y, ctx);
    const sp = startRef.current;
    setRoi({
      x1: Math.min(sp.x, ix),
      y1: Math.min(sp.y, iy),
      x2: Math.max(sp.x, ix),
      y2: Math.max(sp.y, iy),
    });
    setIsDrawing(false);
    startRef.current = null;
  }, []);

  const clearROI = useCallback(() => {
    setRoi(null);
    setIsDrawing(false);
    startRef.current = null;
  }, []);

  return { isDrawing, roi, startDraw, updateDraw, endDraw, clearROI };
}
