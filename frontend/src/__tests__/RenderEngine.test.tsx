jest.mock('../services/light_test_api', () => ({
  analyzeLightTestImage: jest.fn(),
  renderLightTest: jest.fn(),
}));

import { act, render, screen } from '@testing-library/react';
import { configureStore } from '@reduxjs/toolkit';
import { Provider } from 'react-redux';
import RenderEngine from '../components/light_test/RenderEngine';
import * as lightTestApi from '../services/light_test_api';
import type { DepthAnalysisResult, MaterialAnalysisResult } from '../services/light_test_api';
import type { ImageMetadata, LightConfig } from '../services/types';
import lightTestReducer from '../store/slices/lightTestSlice';

const mockRenderLightTest = lightTestApi.renderLightTest as jest.Mock;

const mockCtx = {
  clearRect: jest.fn(),
  drawImage: jest.fn(),
  fillRect: jest.fn(),
  fillStyle: '',
};

beforeAll(() => {
  jest.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(
    mockCtx as unknown as CanvasRenderingContext2D,
  );
});

afterAll(() => {
  jest.restoreAllMocks();
});

const mockImage: ImageMetadata = {
  id: 'img-123',
  original_filename: 'test.png',
  label: '',
  index: 0,
  file_size: 1024,
  upload_timestamp: '2026-01-01T00:00:00Z',
  file_path: 'data/uploads/test.png',
  group: 'analysis',
};

const mockDepthResult: DepthAnalysisResult = {
  status: 'success',
  depth_stats: {
    depth_complexity: 0.5,
    has_shadow_region: false,
    depth_range: 0.5,
    depth_mean: 0.3,
    depth_gradient_max: 0.2,
  },
  depth_map_shape: [64, 64],
  depth_map_base64: 'fakeDepthBase64==',
  error_message: null,
};

const mockMaterialResult: MaterialAnalysisResult = {
  status: 'success',
  surface_type: 'metal',
  material_map: null,
  confidence: 0.9,
  error_message: null,
};

const mockLight: LightConfig = {
  id: 'light-1',
  type: 'led',
  shape: 'ring',
  position: { x: 0, y: -200, z: 400 },
  intensity: 80,
  color: { r: 255, g: 255, b: 255 },
  polarizer: false,
  pitch: 45,
  yaw: 0,
  lwd: 300,
  size: { width: 100, height: 100 },
};

type LightTestPreloaded = {
  light_test: {
    image: ImageMetadata | null;
    lights: LightConfig[];
    camera_view: 'front' | 'top';
    rendered_result: string | null;
    analysis_status: 'idle' | 'loading' | 'success' | 'partial' | 'error';
    depth_result: DepthAnalysisResult | null;
    material_result: MaterialAnalysisResult | null;
    analysis_error: string | null;
    selected_light_id: string | null;
    lens_polarizer_angle: number;
    is_grayscale: boolean;
  };
};

const defaultState: LightTestPreloaded['light_test'] = {
  image: null,
  lights: [],
  camera_view: 'front',
  rendered_result: null,
  analysis_status: 'idle',
  depth_result: null,
  material_result: null,
  analysis_error: null,
  selected_light_id: null,
  lens_polarizer_angle: 0,
  is_grayscale: false,
};

const makeStore = (overrides?: Partial<LightTestPreloaded['light_test']>) =>
  configureStore({
    reducer: { light_test: lightTestReducer },
    preloadedState: { light_test: { ...defaultState, ...overrides } },
  });

const renderWithStore = (overrides?: Partial<LightTestPreloaded['light_test']>) => {
  const store = makeStore(overrides);
  return { ...render(<Provider store={store}><RenderEngine /></Provider>), store };
};

describe('RenderEngine', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockRenderLightTest.mockResolvedValue({ rendered_image: 'renderedBase64==' });
  });

  it('renders without crash', () => {
    const { container } = renderWithStore();
    expect(container).toBeTruthy();
  });

  it('shows hint when no depth data', () => {
    renderWithStore({ image: mockImage, lights: [mockLight], depth_result: null });
    expect(screen.getByTestId('render-engine-hint')).toBeInTheDocument();
  });

  it('shows hint when no lights', () => {
    renderWithStore({ image: mockImage, lights: [], depth_result: mockDepthResult });
    expect(screen.getByTestId('render-engine-hint')).toBeInTheDocument();
  });

  it('shows hint when no image', () => {
    renderWithStore({ image: null, lights: [mockLight], depth_result: mockDepthResult });
    expect(screen.getByTestId('render-engine-hint')).toBeInTheDocument();
  });

  it('shows render-engine element when image, depth, and lights are present', () => {
    renderWithStore({
      image: mockImage,
      lights: [mockLight],
      depth_result: mockDepthResult,
      material_result: mockMaterialResult,
    });
    expect(screen.getByTestId('render-engine')).toBeInTheDocument();
  });

  it('does not show render-engine-hint when all conditions are met', () => {
    renderWithStore({
      image: mockImage,
      lights: [mockLight],
      depth_result: mockDepthResult,
      material_result: mockMaterialResult,
    });
    expect(screen.queryByTestId('render-engine-hint')).not.toBeInTheDocument();
  });

  it('calls renderLightTest after debounce when conditions are met', async () => {
    jest.useFakeTimers();
    renderWithStore({
      image: mockImage,
      lights: [mockLight],
      depth_result: mockDepthResult,
      material_result: mockMaterialResult,
    });
    await act(async () => {
      jest.advanceTimersByTime(300);
      await Promise.resolve();
    });
    expect(mockRenderLightTest).toHaveBeenCalled();
    jest.useRealTimers();
  });

  it('does not call renderLightTest when depth is missing', async () => {
    jest.useFakeTimers();
    renderWithStore({ image: mockImage, lights: [mockLight], depth_result: null });
    await act(async () => {
      jest.advanceTimersByTime(300);
      await Promise.resolve();
    });
    expect(mockRenderLightTest).not.toHaveBeenCalled();
    jest.useRealTimers();
  });

  it('shows render-engine-canvas element when rendering conditions met', () => {
    renderWithStore({
      image: mockImage,
      lights: [mockLight],
      depth_result: mockDepthResult,
      material_result: mockMaterialResult,
    });
    expect(screen.getByTestId('render-engine-canvas')).toBeInTheDocument();
  });

  it('renders loading indicator during API call', async () => {
    let resolveRender!: (value: { rendered_image: string }) => void;
    mockRenderLightTest.mockReturnValue(
      new Promise<{ rendered_image: string }>(resolve => { resolveRender = resolve; }),
    );
    jest.useFakeTimers();
    renderWithStore({
      image: mockImage,
      lights: [mockLight],
      depth_result: mockDepthResult,
      material_result: mockMaterialResult,
    });
    await act(async () => {
      jest.advanceTimersByTime(300);
      await Promise.resolve();
    });
    expect(screen.getByTestId('render-loading')).toBeInTheDocument();
    await act(async () => { resolveRender({ rendered_image: 'done' }); });
    jest.useRealTimers();
  });
});
