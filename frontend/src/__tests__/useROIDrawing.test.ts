import { renderHook, act } from '@testing-library/react';
import { useROIDrawing } from '../hooks/useROIDrawing';
import type { DrawContext } from '../hooks/useROIDrawing';

// CTX_HALF: 1600x1200 image in 800x600 canvas
// scale = min(800/1600, 600/1200) = 0.5, offsetX=0, offsetY=0
const CTX_HALF: DrawContext = { canvasWidth: 800, canvasHeight: 600, imageWidth: 1600, imageHeight: 1200 };

// CTX_PILLAR: 400x400 image in 800x400 canvas (wide canvas → pillarboxing)
// scale = min(800/400, 400/400) = 1, displayW=400
// offsetX = (800-400)/2 = 200, offsetY = 0
const CTX_PILLAR: DrawContext = { canvasWidth: 800, canvasHeight: 400, imageWidth: 400, imageHeight: 400 };

// CTX_LETTER: 800x400 image in 800x600 canvas (tall canvas → letterboxing)
// scale = min(800/800, 600/400) = 1, displayH=400
// offsetX = 0, offsetY = (600-400)/2 = 100
const CTX_LETTER: DrawContext = { canvasWidth: 800, canvasHeight: 600, imageWidth: 800, imageHeight: 400 };

// CTX_UNIT: 800x600 image in 800x600 canvas (1:1, no offsets)
const CTX_UNIT: DrawContext = { canvasWidth: 800, canvasHeight: 600, imageWidth: 800, imageHeight: 600 };

describe('useROIDrawing — initial state', () => {
  it('starts with isDrawing=false', () => {
    const { result } = renderHook(() => useROIDrawing());
    expect(result.current.isDrawing).toBe(false);
  });

  it('starts with roi=null', () => {
    const { result } = renderHook(() => useROIDrawing());
    expect(result.current.roi).toBeNull();
  });

  it('exposes startDraw, updateDraw, endDraw, clearROI functions', () => {
    const { result } = renderHook(() => useROIDrawing());
    expect(typeof result.current.startDraw).toBe('function');
    expect(typeof result.current.updateDraw).toBe('function');
    expect(typeof result.current.endDraw).toBe('function');
    expect(typeof result.current.clearROI).toBe('function');
  });
});

describe('useROIDrawing — startDraw', () => {
  it('sets isDrawing to true', () => {
    const { result } = renderHook(() => useROIDrawing());
    act(() => { result.current.startDraw(100, 100, CTX_HALF); });
    expect(result.current.isDrawing).toBe(true);
  });

  it('initializes roi as a point at start coords (scaled)', () => {
    const { result } = renderHook(() => useROIDrawing());
    // canvas (100, 100) with scale=0.5 → image (200, 200)
    act(() => { result.current.startDraw(100, 100, CTX_HALF); });
    expect(result.current.roi).toEqual({ x1: 200, y1: 200, x2: 200, y2: 200 });
  });
});

describe('useROIDrawing — updateDraw', () => {
  it('updates roi while drawing', () => {
    const { result } = renderHook(() => useROIDrawing());
    act(() => { result.current.startDraw(100, 100, CTX_HALF); });
    // canvas (200, 200) with scale=0.5 → image (400, 400)
    act(() => { result.current.updateDraw(200, 200, CTX_HALF); });
    expect(result.current.roi).toEqual({ x1: 200, y1: 200, x2: 400, y2: 400 });
  });

  it('does nothing if not drawing', () => {
    const { result } = renderHook(() => useROIDrawing());
    act(() => { result.current.updateDraw(200, 200, CTX_HALF); });
    expect(result.current.roi).toBeNull();
    expect(result.current.isDrawing).toBe(false);
  });

  it('keeps isDrawing true during update', () => {
    const { result } = renderHook(() => useROIDrawing());
    act(() => { result.current.startDraw(0, 0, CTX_HALF); });
    act(() => { result.current.updateDraw(100, 100, CTX_HALF); });
    expect(result.current.isDrawing).toBe(true);
  });
});

describe('useROIDrawing — endDraw', () => {
  it('sets isDrawing to false', () => {
    const { result } = renderHook(() => useROIDrawing());
    act(() => { result.current.startDraw(0, 0, CTX_HALF); });
    act(() => { result.current.endDraw(200, 200, CTX_HALF); });
    expect(result.current.isDrawing).toBe(false);
  });

  it('finalizes roi at end coordinates', () => {
    const { result } = renderHook(() => useROIDrawing());
    // start: canvas (0,0) → image (0,0)
    // end: canvas (400,300) → image (800,600)
    act(() => { result.current.startDraw(0, 0, CTX_HALF); });
    act(() => { result.current.endDraw(400, 300, CTX_HALF); });
    expect(result.current.roi).toEqual({ x1: 0, y1: 0, x2: 800, y2: 600 });
  });

  it('does nothing if not drawing', () => {
    const { result } = renderHook(() => useROIDrawing());
    act(() => { result.current.endDraw(200, 200, CTX_HALF); });
    expect(result.current.roi).toBeNull();
  });
});

describe('useROIDrawing — clearROI', () => {
  it('resets roi to null', () => {
    const { result } = renderHook(() => useROIDrawing());
    act(() => { result.current.startDraw(0, 0, CTX_HALF); });
    act(() => { result.current.endDraw(200, 200, CTX_HALF); });
    act(() => { result.current.clearROI(); });
    expect(result.current.roi).toBeNull();
  });

  it('sets isDrawing to false', () => {
    const { result } = renderHook(() => useROIDrawing());
    act(() => { result.current.startDraw(0, 0, CTX_HALF); });
    act(() => { result.current.clearROI(); });
    expect(result.current.isDrawing).toBe(false);
  });
});

describe('useROIDrawing — coordinate conversion (scale)', () => {
  it('converts canvas coords to image coords using scale factor', () => {
    // CTX_HALF: scale=0.5, no offsets
    // canvas (400, 300) → image (800, 600)
    const { result } = renderHook(() => useROIDrawing());
    act(() => { result.current.startDraw(0, 0, CTX_HALF); });
    act(() => { result.current.endDraw(400, 300, CTX_HALF); });
    expect(result.current.roi).toEqual({ x1: 0, y1: 0, x2: 800, y2: 600 });
  });

  it('produces integer coordinates (Math.round)', () => {
    // canvas (1, 1) with scale=0.5 → image (2, 2) exactly (already integer)
    const { result } = renderHook(() => useROIDrawing());
    act(() => { result.current.startDraw(1, 1, CTX_HALF); });
    act(() => { result.current.endDraw(3, 3, CTX_HALF); });
    const roi = result.current.roi!;
    expect(Number.isInteger(roi.x1)).toBe(true);
    expect(Number.isInteger(roi.y1)).toBe(true);
    expect(Number.isInteger(roi.x2)).toBe(true);
    expect(Number.isInteger(roi.y2)).toBe(true);
  });

  it('1:1 scale produces identity mapping', () => {
    const { result } = renderHook(() => useROIDrawing());
    act(() => { result.current.startDraw(100, 50, CTX_UNIT); });
    act(() => { result.current.endDraw(300, 200, CTX_UNIT); });
    expect(result.current.roi).toEqual({ x1: 100, y1: 50, x2: 300, y2: 200 });
  });
});

describe('useROIDrawing — pillarboxing offset', () => {
  it('subtracts offsetX from canvas x before scaling', () => {
    // CTX_PILLAR: scale=1, offsetX=200, offsetY=0
    // canvas (200, 0) → image (0, 0) — left edge of image
    // canvas (600, 400) → image (400, 400) — right-bottom corner
    const { result } = renderHook(() => useROIDrawing());
    act(() => { result.current.startDraw(200, 0, CTX_PILLAR); });
    act(() => { result.current.endDraw(600, 400, CTX_PILLAR); });
    expect(result.current.roi).toEqual({ x1: 0, y1: 0, x2: 400, y2: 400 });
  });
});

describe('useROIDrawing — letterboxing offset', () => {
  it('subtracts offsetY from canvas y before scaling', () => {
    // CTX_LETTER: scale=1, offsetX=0, offsetY=100
    // canvas (0, 100) → image (0, 0) — top-left of image
    // canvas (800, 500) → image (800, 400) — bottom-right
    const { result } = renderHook(() => useROIDrawing());
    act(() => { result.current.startDraw(0, 100, CTX_LETTER); });
    act(() => { result.current.endDraw(800, 500, CTX_LETTER); });
    expect(result.current.roi).toEqual({ x1: 0, y1: 0, x2: 800, y2: 400 });
  });
});

describe('useROIDrawing — boundary clamping', () => {
  it('clamps negative canvas coords to image origin (0,0)', () => {
    // canvas (-10, -10) should clamp to image (0, 0)
    const { result } = renderHook(() => useROIDrawing());
    act(() => { result.current.startDraw(-10, -10, CTX_HALF); });
    expect(result.current.roi!.x1).toBe(0);
    expect(result.current.roi!.y1).toBe(0);
  });

  it('clamps coords beyond canvas to image max dimensions', () => {
    // canvas (900, 700) with scale=0.5 → raw (1800, 1400), clamped to (1600, 1200)
    const { result } = renderHook(() => useROIDrawing());
    act(() => { result.current.startDraw(0, 0, CTX_HALF); });
    act(() => { result.current.endDraw(900, 700, CTX_HALF); });
    expect(result.current.roi!.x2).toBe(1600);
    expect(result.current.roi!.y2).toBe(1200);
  });

  it('clamps pillarbox area to image x=0 when click is left of image', () => {
    // CTX_PILLAR: offsetX=200; canvas (0, 0) → raw x=(0-200)/1=-200 → clamped 0
    const { result } = renderHook(() => useROIDrawing());
    act(() => { result.current.startDraw(0, 0, CTX_PILLAR); });
    expect(result.current.roi!.x1).toBe(0);
  });

  it('clamps pillarbox area to image x=max when click is right of image', () => {
    // CTX_PILLAR: offsetX=200; canvas (850, 0) → raw x=(850-200)/1=650 → clamped 400
    const { result } = renderHook(() => useROIDrawing());
    act(() => { result.current.startDraw(0, 0, CTX_PILLAR); });
    act(() => { result.current.endDraw(850, 400, CTX_PILLAR); });
    expect(result.current.roi!.x2).toBe(400);
  });
});

describe('useROIDrawing — ROI normalization (x1<x2, y1<y2)', () => {
  it('normalizes when drawn right-to-left', () => {
    // start at x=400, end at x=100 → x1=100, x2=400 (not x1=400)
    const { result } = renderHook(() => useROIDrawing());
    act(() => { result.current.startDraw(200, 100, CTX_UNIT); });
    act(() => { result.current.endDraw(100, 50, CTX_UNIT); });
    const roi = result.current.roi!;
    expect(roi.x1).toBeLessThanOrEqual(roi.x2);
    expect(roi.y1).toBeLessThanOrEqual(roi.y2);
  });

  it('normalizes when drawn bottom-to-top', () => {
    const { result } = renderHook(() => useROIDrawing());
    act(() => { result.current.startDraw(100, 300, CTX_UNIT); });
    act(() => { result.current.endDraw(400, 100, CTX_UNIT); });
    const roi = result.current.roi!;
    expect(roi.y1).toBeLessThanOrEqual(roi.y2);
  });
});
