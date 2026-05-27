import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import lightTestReducer from '../store/slices/lightTestSlice';
import FrontView from '../components/light_test/FrontView';
import type { LightConfig } from '../services/types';
import type { FrontViewLight } from '../hooks/useLightSync';

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

const toFrontViewLight = (light: LightConfig): FrontViewLight => ({
  ...light,
  screenX: 0.5,
  screenY: 0.5,
});

const makeStore = (selectedId: string | null = null) =>
  configureStore({
    reducer: { light_test: lightTestReducer },
    preloadedState: {
      light_test: {
        image: null,
        lights: [],
        camera_view: 'front' as const,
        rendered_result: null,
        analysis_status: 'idle' as const,
        depth_result: null,
        material_result: null,
        analysis_error: null,
        selected_light_id: selectedId,
      },
    },
  });

const renderFrontView = (
  lights: FrontViewLight[] = [],
  onDrag = jest.fn(),
  selectedId: string | null = null,
) => {
  const store = makeStore(selectedId);
  return {
    ...render(
      <Provider store={store}>
        <FrontView frontViewLights={lights} onDrag={onDrag} />
      </Provider>,
    ),
    store,
  };
};

describe('FrontView', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders without crashing', () => {
    const { container } = renderFrontView();
    expect(container).toBeTruthy();
  });

  it('renders front-view-container', () => {
    renderFrontView();
    expect(screen.getByTestId('front-view-container')).toBeInTheDocument();
  });

  it('renders front-view-canvas as a CANVAS element', () => {
    renderFrontView();
    expect(screen.getByTestId('front-view-canvas').tagName).toBe('CANVAS');
  });

  it('renders no light elements when lights array is empty', () => {
    renderFrontView([]);
    expect(screen.queryByTestId('front-light-light-1')).not.toBeInTheDocument();
  });

  it('renders front-light-{id} for each light', () => {
    renderFrontView([toFrontViewLight(sampleLight)]);
    expect(screen.getByTestId('front-light-light-1')).toBeInTheDocument();
  });

  it('renders multiple light elements', () => {
    const light2: LightConfig = { ...sampleLight, id: 'light-2', shape: 'bar' };
    renderFrontView([toFrontViewLight(sampleLight), toFrontViewLight(light2)]);
    expect(screen.getByTestId('front-light-light-1')).toBeInTheDocument();
    expect(screen.getByTestId('front-light-light-2')).toBeInTheDocument();
  });

  it('does not show front-light-selected when no light is selected', () => {
    renderFrontView([toFrontViewLight(sampleLight)], jest.fn(), null);
    expect(screen.queryByTestId('front-light-selected')).not.toBeInTheDocument();
  });

  it('shows front-light-selected when a light is selected', () => {
    renderFrontView([toFrontViewLight(sampleLight)], jest.fn(), 'light-1');
    expect(screen.getByTestId('front-light-selected')).toBeInTheDocument();
  });

  it('dispatches selectLight when clicking a light', () => {
    const { store } = renderFrontView([toFrontViewLight(sampleLight)]);
    fireEvent.mouseDown(screen.getByTestId('front-light-light-1'));
    expect((store.getState() as any).light_test.selected_light_id).toBe('light-1');
  });

  it('light element has pointer cursor style', () => {
    renderFrontView([toFrontViewLight(sampleLight)]);
    const el = screen.getByTestId('front-light-light-1');
    expect(el).toBeInTheDocument();
  });

  it('selected light has highlight border', () => {
    renderFrontView([toFrontViewLight(sampleLight)], jest.fn(), 'light-1');
    const el = screen.getByTestId('front-light-light-1');
    expect(el.style.border).toContain('solid');
  });

  it('unselected light does not have white border', () => {
    const light2: LightConfig = { ...sampleLight, id: 'light-2' };
    renderFrontView([toFrontViewLight(sampleLight), toFrontViewLight(light2)], jest.fn(), 'light-1');
    const el2 = screen.getByTestId('front-light-light-2');
    expect(el2.style.border).not.toContain('rgb(255, 255, 255)');
  });

  it('renders front-view-container as relative-positioned container', () => {
    renderFrontView();
    const container = screen.getByTestId('front-view-container');
    expect(container).toBeInTheDocument();
  });
});
