import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import lightTestReducer from '../store/slices/lightTestSlice';
import DualViewLayout from '../components/light_test/DualViewLayout';
import type { ImageMetadata } from '../services/types';

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

const makeStore = (preloadedState?: { light_test: { image: ImageMetadata | null; lights: []; camera_view: 'front' | 'top'; rendered_result: null } }) =>
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

  it('shows "Depth data required" text in top view', () => {
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
      light_test: { image: mockImage, lights: [], camera_view: 'front', rendered_result: null },
    });
    renderWithStore(store);
    expect(screen.getByTestId('dual-view-layout')).toBeInTheDocument();
    expect(screen.getByTestId('front-view-canvas').tagName).toBe('CANVAS');
  });
});
