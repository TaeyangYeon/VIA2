import axios from 'axios';

const api = axios.create({ baseURL: 'http://localhost:8000' });

export interface DepthAnalysisResult {
  status: 'success' | 'error';
  depth_stats: {
    depth_complexity: number;
    has_shadow_region: boolean;
    depth_range: number;
    depth_mean: number;
    depth_gradient_max: number;
  } | null;
  depth_map_shape: [number, number] | null;
  depth_map_base64: string | null;
  error_message: string | null;
}

export interface MaterialAnalysisResult {
  status: 'success' | 'error';
  surface_type: string | null;
  material_map: Record<string, unknown> | null;
  confidence: number | null;
  error_message: string | null;
}

export interface LightTestAnalysisResponse {
  status: 'success' | 'partial' | 'error';
  depth: DepthAnalysisResult;
  material: MaterialAnalysisResult;
}

export async function analyzeLightTestImage(file: File): Promise<LightTestAnalysisResponse> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post<LightTestAnalysisResponse>(
    '/api/light_test/analyze',
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );
  return response.data;
}

export interface RenderLightTestRequest {
  image_id: string;
  depth_map_base64: string | null;
  lights: import('./types').LightConfig[];
  surface_type: string;
  lens_polarizer_angle: number;
}

export interface RenderLightTestResponse {
  rendered_image: string;
}

export async function renderLightTest(
  request: RenderLightTestRequest,
): Promise<RenderLightTestResponse> {
  const response = await api.post<RenderLightTestResponse>(
    '/api/light_test/render',
    request,
  );
  return response.data;
}
