import { Loader } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useAppDispatch, useAppSelector } from '../../store';
import { setRenderedResult } from '../../store/slices/lightTestSlice';
import { renderLightTest } from '../../services/light_test_api';

export default function RenderEngine() {
  const dispatch = useAppDispatch();
  const image = useAppSelector(s => s.light_test.image);
  const depth_result = useAppSelector(s => s.light_test.depth_result);
  const lights = useAppSelector(s => s.light_test.lights);
  const material_result = useAppSelector(s => s.light_test.material_result);
  const rendered_result = useAppSelector(s => s.light_test.rendered_result);

  const [isLoading, setIsLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const hasImage = image != null;
  const hasDepth = depth_result?.depth_map_base64 != null;
  const hasLights = lights.length > 0;

  // Trigger PBR render (debounced 200 ms) whenever inputs change
  useEffect(() => {
    if (!hasImage || !hasDepth || !hasLights) {
      dispatch(setRenderedResult(null));
      return;
    }

    if (debounceRef.current) clearTimeout(debounceRef.current);

    debounceRef.current = setTimeout(async () => {
      setIsLoading(true);
      try {
        const response = await renderLightTest({
          image_id: image!.id,
          depth_map_base64: depth_result!.depth_map_base64!,
          lights,
          surface_type: material_result?.surface_type ?? 'default',
        });
        dispatch(setRenderedResult(response.rendered_image));
      } catch {
        // Silently ignore render errors — original FrontView stays visible
      } finally {
        setIsLoading(false);
      }
    }, 200);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [image, lights, depth_result, material_result, dispatch, hasImage, hasDepth, hasLights]);

  // Paint rendered image onto canvas whenever the result changes
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !rendered_result) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const img = new window.Image();
    img.onload = () => {
      canvas.width = img.naturalWidth || canvas.offsetWidth;
      canvas.height = img.naturalHeight || canvas.offsetHeight;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    };
    img.src = `data:image/png;base64,${rendered_result}`;
  }, [rendered_result]);

  // Hint badge when prerequisites are missing
  if (!hasImage || !hasDepth || !hasLights) {
    const msg = !hasImage
      ? 'Upload image to enable rendering'
      : !hasDepth
        ? 'Run analysis to enable rendering'
        : 'Add lights to enable rendering';
    return (
      <div
        data-testid="render-engine-hint"
        style={{
          position: 'absolute',
          bottom: '8px',
          left: '50%',
          transform: 'translateX(-50%)',
          pointerEvents: 'none',
          zIndex: 5,
        }}
        className="bg-white/5 backdrop-blur border border-white/10 rounded px-2 py-1"
      >
        <span className="text-xs" style={{ color: '#707070' }}>{msg}</span>
      </div>
    );
  }

  return (
    <div
      data-testid="render-engine"
      style={{ position: 'absolute', inset: 0 }}
      className="bg-white/5 backdrop-blur border border-white/10 transition-all duration-150"
    >
      {isLoading && (
        <div
          data-testid="render-loading"
          style={{
            position: 'absolute',
            top: '8px',
            right: '8px',
            zIndex: 10,
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          }}
          className="bg-white/5 backdrop-blur border border-white/10 rounded px-2 py-1"
        >
          <Loader size={10} className="animate-spin" style={{ color: '#a0a0a0' }} />
          <span className="text-xs" style={{ color: '#a0a0a0' }}>Rendering…</span>
        </div>
      )}
      <canvas
        data-testid="render-engine-canvas"
        ref={canvasRef}
        style={{ display: 'block', width: '100%', height: '100%' }}
      />
    </div>
  );
}
