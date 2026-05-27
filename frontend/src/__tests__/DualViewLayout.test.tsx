import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import lightTestReducer from '../store/slices/lightTestSlice';
import DualViewLayout from '../components/light_test/DualViewLayout';
import type { ImageMetadata } from '../services/types';
import type { DepthAnalysisResult, MaterialAnalysisResult } from '../services/light_test_api';

const mockCtx = {
  clearRect: jest.fn(),
  drawImage: jest.fn(),
  fillRect: jest.fn(),
  strokeRect: jest.fn(),
  setLineDash: jest.fn(),
  save: jest.fn(),
  restore: jest.fn(),
  beginPath: jest.fn(),
  moveTo: jest.fn(),
  lineTo: jest.fn(),
  stroke: jest.fn(),
  fill: jest.fn(),
  fillStyle: '',
  strokeStyle: '',
  lineWidth: 0,
  globalAlpha: 1,
  font: '',
  textAlign: '',
  fillText: jest.fn(),
  measureText: jest.fn().mockReturnValue({ width: 100 }),
};

beforeAll(() => {
  jest.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(mockCtx as unknown as CanvasRenderingContext2D);
});

afterAll(() => {
  jest.restoreAllMocks();
});

const mockImage: ImageMetadata = {
  id: 'lt-456',
  original_filename: 'scene.png',
  label: '',
  index: 0,
  file_size: 20480,
  upload_timestamp: '2026-01-01T00:00:00Z',
  file_path: '/images/scene.png',
  group: 'light_test',
};

const mockDepthResult: DepthAnalysisResult = {
  status: 'success',
  depth_stats: {
    depth_complexity: 0.5,
    has_shadow_region: true,
    depth_range: 0.8,
    depth_mean: 0.4,
    depth_gradient_max: 0.35,
  },
  depth_map_shape: [100, 100],
  depth_map_base64: 'iVBORw0KGgo=',
  error_message: null,
};

const mockMaterialResult: MaterialAnalysisResult = {
  status: 'success',
  surface_type: 'metal',
  material_map: null,
  confidence: 0.85,
  error_message: null,
};

type LightTestPreloaded = {
  light_test: {
    image: ImageMetadata | null;
    lights: [];
    camera_view: 'front' | 'top';
    rendered_result: string | null;
    analysis_status: 'idle' | 'loading' | 'success' | 'partial' | 'error';
    depth_result: DepthAnalysisResult | null;
    material_result: MaterialAnalysisResult | null;
    analysis_error: string | null;
    selected_light_id: string | null;
  };
};

const makeStore = (preloadedState?: LightTestPreloaded) =>
  configureStore({
    reducer: { light_test: lightTestReducer },
    preloadedState,
  });

const renderWithStore = (storeOverride?: ReturnType<typeof makeStore>) => {
  const s = storeOverride ?? makeStore();
  return { ...render(<Provider store={s}><DualViewLayout /></Provider>), store: s };
};

describe('DualViewLayout', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders without crashing', () => {
    const { container } = renderWithStore();
    expect(container).toBeTruthy();
  });

  it('has data-testid="dual-view-layout"', () => {
    renderWithStore();
    expect(screen.getByTestId('dual-view-layout')).toBeInTheDocument();
  });

  it('renders front-view-panel', () => {
    renderWithStore();
    expect(screen.getByTestId('front-view-panel')).toBeInTheDocument();
  });

  it('renders top-view-panel', () => {
    renderWithStore();
    expect(screen.getByTestId('top-view-panel')).toBeInTheDocument();
  });

  it('renders light-controls-panel', () => {
    renderWithStore();
    expect(screen.getByTestId('light-controls-panel')).toBeInTheDocument();
  });

  it('shows "정면도" label for front view', () => {
    renderWithStore();
    expect(screen.getByText(/정면도/)).toBeInTheDocument();
  });

  it('shows "평면도" label for top view', () => {
    renderWithStore();
    expect(screen.getByText(/평면도/)).toBeInTheDocument();
  });

  it('renders front-view-canvas as a canvas element', () => {
    renderWithStore();
    const canvas = screen.getByTestId('front-view-canvas');
    expect(canvas.tagName).toBe('CANVAS');
  });

  it('renders top-view-canvas as a canvas element', () => {
    renderWithStore();
    const canvas = screen.getByTestId('top-view-canvas');
    expect(canvas.tagName).toBe('CANVAS');
  });

  it('shows "Depth data required" text when no depth result', () => {
    renderWithStore();
    expect(screen.getByText(/Depth data required/i)).toBeInTheDocument();
  });

  it('shows "Controls will appear here" in light controls', () => {
    renderWithStore();
    expect(screen.getByText(/Controls will appear here/i)).toBeInTheDocument();
  });

  it('renders add-light-btn', () => {
    renderWithStore();
    expect(screen.getByTestId('add-light-btn')).toBeInTheDocument();
  });

  it('shows "Light Controls" label', () => {
    renderWithStore();
    expect(screen.getByText(/Light Controls/i)).toBeInTheDocument();
  });

  it('renders "Front View" label text', () => {
    renderWithStore();
    expect(screen.getByText(/Front View/i)).toBeInTheDocument();
  });

  it('renders with image preloaded in redux store', () => {
    const store = makeStore({
      light_test: {
        image: mockImage,
        lights: [],
        camera_view: 'front',
        rendered_result: null,
        analysis_status: 'idle',
        depth_result: null,
        material_result: null,
        analysis_error: null,
        selected_light_id: null,
      },
    });
    renderWithStore(store);
    expect(screen.getByTestId('dual-view-layout')).toBeInTheDocument();
    expect(screen.getByTestId('front-view-canvas').tagName).toBe('CANVAS');
  });

  // ── Depth/material result display tests ────────────────────────────────────

  it('hides "Depth data required" when depth result is available', () => {
    const store = makeStore({
      light_test: {
        image: mockImage,
        lights: [],
        camera_view: 'front',
        rendered_result: null,
        analysis_status: 'success',
        depth_result: mockDepthResult,
        material_result: null,
        analysis_error: null,
        selected_light_id: null,
      },
    });
    renderWithStore(store);
    expect(screen.queryByText(/Depth data required/i)).not.toBeInTheDocument();
  });

  it('shows surface-type-badge when material result has surface_type', () => {
    const store = makeStore({
      light_test: {
        image: mockImage,
        lights: [],
        camera_view: 'front',
        rendered_result: null,
        analysis_status: 'success',
        depth_result: null,
        material_result: mockMaterialResult,
        analysis_error: null,
        selected_light_id: null,
      },
    });
    renderWithStore(store);
    expect(screen.getByTestId('surface-type-badge')).toBeInTheDocument();
  });

  it('surface-type-badge shows correct surface type text', () => {
    const store = makeStore({
      light_test: {
        image: mockImage,
        lights: [],
        camera_view: 'front',
        rendered_result: null,
        analysis_status: 'success',
        depth_result: null,
        material_result: mockMaterialResult,
        analysis_error: null,
        selected_light_id: null,
      },
    });
    renderWithStore(store);
    expect(screen.getByTestId('surface-type-badge')).toHaveTextContent('metal');
  });

  it('does not show surface-type-badge when material_result is null', () => {
    renderWithStore();
    expect(screen.queryByTestId('surface-type-badge')).not.toBeInTheDocument();
  });

  it('does not show surface-type-badge when surface_type is null', () => {
    const store = makeStore({
      light_test: {
        image: mockImage,
        lights: [],
        camera_view: 'front',
        rendered_result: null,
        analysis_status: 'error',
        depth_result: null,
        material_result: {
          status: 'error',
          surface_type: null,
          material_map: null,
          confidence: null,
          error_message: 'Failed',
        },
        analysis_error: null,
        selected_light_id: null,
      },
    });
    renderWithStore(store);
    expect(screen.queryByTestId('surface-type-badge')).not.toBeInTheDocument();
  });

  it('shows both depth and material results simultaneously', () => {
    const store = makeStore({
      light_test: {
        image: mockImage,
        lights: [],
        camera_view: 'front',
        rendered_result: null,
        analysis_status: 'success',
        depth_result: mockDepthResult,
        material_result: mockMaterialResult,
        analysis_error: null,
        selected_light_id: null,
      },
    });
    renderWithStore(store);
    expect(screen.queryByText(/Depth data required/i)).not.toBeInTheDocument();
    expect(screen.getByTestId('surface-type-badge')).toBeInTheDocument();
  });
});
