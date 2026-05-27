import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import lightTestReducer from '../store/slices/lightTestSlice';
import TopView from '../components/light_test/TopView';
import type { LightConfig } from '../services/types';
import type { TopViewLight } from '../hooks/useLightSync';
import type { DepthAnalysisResult } from '../services/light_test_api';

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
  arc: jest.fn(),
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
  jest.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(
    mockCtx as unknown as CanvasRenderingContext2D,
  );
});

afterAll(() => {
  jest.restoreAllMocks();
});

const sampleLight: LightConfig = {
  id: 'light-1',
  type: 'led',
  shape: 'ring',
  position: { x: 0, y: 200, z: 0 },
  intensity: 80,
  color: { r: 255, g: 255, b: 255 },
  polarizer: false,
  pitch: 45,
  yaw: 0,
  lwd: 300,
  size: { width: 50, height: 50 },
};

const toTopViewLight = (light: LightConfig): TopViewLight => ({
  ...light,
  screenX: 0.5,
  screenZ: 0.3,
});

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

const makeStore = (opts: {
  depth_result?: DepthAnalysisResult | null;
  selected_light_id?: string | null;
} = {}) =>
  configureStore({
    reducer: { light_test: lightTestReducer },
    preloadedState: {
      light_test: {
        image: null,
        lights: [],
        camera_view: 'front' as const,
        rendered_result: null,
        analysis_status: 'idle' as const,
        depth_result: opts.depth_result ?? null,
        material_result: null,
        analysis_error: null,
        selected_light_id: opts.selected_light_id ?? null,
        lens_polarizer_angle: 0,
        is_grayscale: false,
      },
    },
  });

const renderTopView = (
  lights: TopViewLight[] = [],
  onDrag = jest.fn(),
  storeOpts: Parameters<typeof makeStore>[0] = {},
) => {
  const store = makeStore(storeOpts);
  return {
    ...render(
      <Provider store={store}>
        <TopView topViewLights={lights} onDrag={onDrag} />
      </Provider>,
    ),
    store,
  };
};

describe('TopView', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders without crashing', () => {
    const { container } = renderTopView();
    expect(container).toBeTruthy();
  });

  it('renders top-view-container', () => {
    renderTopView();
    expect(screen.getByTestId('top-view-container')).toBeInTheDocument();
  });

  it('renders top-view-canvas as a CANVAS element', () => {
    renderTopView();
    expect(screen.getByTestId('top-view-canvas').tagName).toBe('CANVAS');
  });

  it('renders top-camera-marker', () => {
    renderTopView();
    expect(screen.getByTestId('top-camera-marker')).toBeInTheDocument();
  });

  it('shows "Depth data required" when no depth result', () => {
    renderTopView();
    expect(screen.getByText(/Depth data required/i)).toBeInTheDocument();
  });

  it('hides "Depth data required" when depth result is available', () => {
    renderTopView([], jest.fn(), { depth_result: mockDepthResult });
    expect(screen.queryByText(/Depth data required/i)).not.toBeInTheDocument();
  });

  it('renders no light elements when lights array is empty', () => {
    renderTopView([]);
    expect(screen.queryByTestId('top-light-light-1')).not.toBeInTheDocument();
  });

  it('renders top-light-{id} for each light', () => {
    renderTopView([toTopViewLight(sampleLight)]);
    expect(screen.getByTestId('top-light-light-1')).toBeInTheDocument();
  });

  it('renders multiple top-light elements', () => {
    const light2: LightConfig = { ...sampleLight, id: 'light-2', shape: 'bar' };
    renderTopView([toTopViewLight(sampleLight), toTopViewLight(light2)]);
    expect(screen.getByTestId('top-light-light-1')).toBeInTheDocument();
    expect(screen.getByTestId('top-light-light-2')).toBeInTheDocument();
  });

  it('dispatches selectLight when clicking a top light', () => {
    const { store } = renderTopView([toTopViewLight(sampleLight)]);
    fireEvent.mouseDown(screen.getByTestId('top-light-light-1'));
    expect((store.getState() as any).light_test.selected_light_id).toBe('light-1');
  });

  it('selected light has highlight border', () => {
    renderTopView([toTopViewLight(sampleLight)], jest.fn(), { selected_light_id: 'light-1' });
    const el = screen.getByTestId('top-light-light-1');
    expect(el.style.border).toContain('solid');
  });

  it('camera marker is visible', () => {
    renderTopView();
    const marker = screen.getByTestId('top-camera-marker');
    expect(marker).toBeInTheDocument();
  });
});
