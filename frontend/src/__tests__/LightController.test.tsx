import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import lightTestReducer from '../store/slices/lightTestSlice';
import LightController from '../components/light_test/LightController';
import type { LightConfig } from '../services/types';
import type { MaterialAnalysisResult } from '../services/light_test_api';

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

const mockMaterial: MaterialAnalysisResult = {
  status: 'success',
  surface_type: 'metal',
  material_map: null,
  confidence: 0.85,
  error_message: null,
};

const makeStore = (opts: {
  lights?: LightConfig[];
  selected_light_id?: string | null;
  material_result?: MaterialAnalysisResult | null;
} = {}) =>
  configureStore({
    reducer: { light_test: lightTestReducer },
    preloadedState: {
      light_test: {
        image: null,
        lights: opts.lights ?? [],
        camera_view: 'front' as const,
        rendered_result: null,
        analysis_status: 'idle' as const,
        depth_result: null,
        material_result: opts.material_result ?? null,
        analysis_error: null,
        selected_light_id: opts.selected_light_id ?? null,
        lens_polarizer_angle: 0,
        is_grayscale: false,
      },
    },
  });

const renderController = (opts: Parameters<typeof makeStore>[0] = {}) => {
  const store = makeStore(opts);
  return {
    ...render(
      <Provider store={store}>
        <LightController />
      </Provider>,
    ),
    store,
  };
};

describe('LightController', () => {
  it('renders without crashing', () => {
    const { container } = renderController();
    expect(container).toBeTruthy();
  });

  it('renders light-controller', () => {
    renderController();
    expect(screen.getByTestId('light-controller')).toBeInTheDocument();
  });

  it('renders add-light-btn', () => {
    renderController();
    expect(screen.getByTestId('add-light-btn')).toBeInTheDocument();
  });

  it('shows "Controls will appear here" when no lights', () => {
    renderController({ lights: [] });
    expect(screen.getByText(/Controls will appear here/i)).toBeInTheDocument();
  });

  it('clicking add-light-btn adds a light to the store', () => {
    const { store } = renderController();
    fireEvent.click(screen.getByTestId('add-light-btn'));
    expect((store.getState() as any).light_test.lights).toHaveLength(1);
  });

  it('new light has default intensity of 80', () => {
    const { store } = renderController();
    fireEvent.click(screen.getByTestId('add-light-btn'));
    expect((store.getState() as any).light_test.lights[0].intensity).toBe(80);
  });

  it('new light has default pitch of 45', () => {
    const { store } = renderController();
    fireEvent.click(screen.getByTestId('add-light-btn'));
    expect((store.getState() as any).light_test.lights[0].pitch).toBe(45);
  });

  it('new light has default lwd of 300', () => {
    const { store } = renderController();
    fireEvent.click(screen.getByTestId('add-light-btn'));
    expect((store.getState() as any).light_test.lights[0].lwd).toBe(300);
  });

  it('renders light-list-item-{id} for each light', () => {
    renderController({ lights: [sampleLight] });
    expect(screen.getByTestId('light-list-item-light-1')).toBeInTheDocument();
  });

  it('renders multiple light list items', () => {
    const light2: LightConfig = { ...sampleLight, id: 'light-2' };
    renderController({ lights: [sampleLight, light2] });
    expect(screen.getByTestId('light-list-item-light-1')).toBeInTheDocument();
    expect(screen.getByTestId('light-list-item-light-2')).toBeInTheDocument();
  });

  it('clicking light-list-item dispatches selectLight', () => {
    const { store } = renderController({ lights: [sampleLight] });
    fireEvent.click(screen.getByTestId('light-list-item-light-1'));
    expect((store.getState() as any).light_test.selected_light_id).toBe('light-1');
  });

  it('does not show selected-light-detail when no light selected', () => {
    renderController({ lights: [sampleLight], selected_light_id: null });
    expect(screen.queryByTestId('selected-light-detail')).not.toBeInTheDocument();
  });

  it('shows selected-light-detail when a light is selected', () => {
    renderController({ lights: [sampleLight], selected_light_id: 'light-1' });
    expect(screen.getByTestId('selected-light-detail')).toBeInTheDocument();
  });

  it('shows remove-light-btn when a light is selected', () => {
    renderController({ lights: [sampleLight], selected_light_id: 'light-1' });
    expect(screen.getByTestId('remove-light-btn')).toBeInTheDocument();
  });

  it('does not show remove-light-btn when no light is selected', () => {
    renderController({ lights: [sampleLight], selected_light_id: null });
    expect(screen.queryByTestId('remove-light-btn')).not.toBeInTheDocument();
  });

  it('clicking remove-light-btn dispatches removeLight', () => {
    const { store } = renderController({ lights: [sampleLight], selected_light_id: 'light-1' });
    fireEvent.click(screen.getByTestId('remove-light-btn'));
    expect((store.getState() as any).light_test.lights).toHaveLength(0);
  });

  it('shows shape-select in selected-light-detail', () => {
    renderController({ lights: [sampleLight], selected_light_id: 'light-1' });
    expect(screen.getByTestId('shape-select')).toBeInTheDocument();
  });

  it('shows type-select in selected-light-detail', () => {
    renderController({ lights: [sampleLight], selected_light_id: 'light-1' });
    expect(screen.getByTestId('type-select')).toBeInTheDocument();
  });

  it('shows pos-x input in selected-light-detail', () => {
    renderController({ lights: [sampleLight], selected_light_id: 'light-1' });
    expect(screen.getByTestId('pos-x')).toBeInTheDocument();
  });

  it('shows pos-y input in selected-light-detail', () => {
    renderController({ lights: [sampleLight], selected_light_id: 'light-1' });
    expect(screen.getByTestId('pos-y')).toBeInTheDocument();
  });

  it('shows pos-z input in selected-light-detail', () => {
    renderController({ lights: [sampleLight], selected_light_id: 'light-1' });
    expect(screen.getByTestId('pos-z')).toBeInTheDocument();
  });

  it('shows angle-pitch input in selected-light-detail', () => {
    renderController({ lights: [sampleLight], selected_light_id: 'light-1' });
    expect(screen.getByTestId('angle-pitch')).toBeInTheDocument();
  });

  it('shows angle-yaw input in selected-light-detail', () => {
    renderController({ lights: [sampleLight], selected_light_id: 'light-1' });
    expect(screen.getByTestId('angle-yaw')).toBeInTheDocument();
  });

  it('shows lwd-input in selected-light-detail', () => {
    renderController({ lights: [sampleLight], selected_light_id: 'light-1' });
    expect(screen.getByTestId('lwd-input')).toBeInTheDocument();
  });

  it('shows intensity-slider in selected-light-detail', () => {
    renderController({ lights: [sampleLight], selected_light_id: 'light-1' });
    expect(screen.getByTestId('intensity-slider')).toBeInTheDocument();
  });

  it('changing shape-select dispatches updateLight', () => {
    const { store } = renderController({ lights: [sampleLight], selected_light_id: 'light-1' });
    fireEvent.change(screen.getByTestId('shape-select'), { target: { value: 'bar' } });
    expect((store.getState() as any).light_test.lights[0].shape).toBe('bar');
  });

  it('changing intensity-slider dispatches updateLight', () => {
    const { store } = renderController({ lights: [sampleLight], selected_light_id: 'light-1' });
    fireEvent.change(screen.getByTestId('intensity-slider'), { target: { value: '50' } });
    expect((store.getState() as any).light_test.lights[0].intensity).toBe(50);
  });

  it('changing pos-x dispatches updateLight', () => {
    const { store } = renderController({ lights: [sampleLight], selected_light_id: 'light-1' });
    fireEvent.change(screen.getByTestId('pos-x'), { target: { value: '100' } });
    expect((store.getState() as any).light_test.lights[0].position.x).toBe(100);
  });

  it('changing type-select dispatches updateLight', () => {
    const { store } = renderController({ lights: [sampleLight], selected_light_id: 'light-1' });
    fireEvent.change(screen.getByTestId('type-select'), { target: { value: 'uv' } });
    expect((store.getState() as any).light_test.lights[0].type).toBe('uv');
  });

  it('changing angle-pitch dispatches updateLight', () => {
    const { store } = renderController({ lights: [sampleLight], selected_light_id: 'light-1' });
    fireEvent.change(screen.getByTestId('angle-pitch'), { target: { value: '30' } });
    expect((store.getState() as any).light_test.lights[0].pitch).toBe(30);
  });

  it('changing lwd-input dispatches updateLight', () => {
    const { store } = renderController({ lights: [sampleLight], selected_light_id: 'light-1' });
    fireEvent.change(screen.getByTestId('lwd-input'), { target: { value: '500' } });
    expect((store.getState() as any).light_test.lights[0].lwd).toBe(500);
  });

  it('shows surface-type-badge when material_result has surface_type', () => {
    renderController({ material_result: mockMaterial });
    expect(screen.getByTestId('surface-type-badge')).toBeInTheDocument();
  });

  it('does not show surface-type-badge when material_result is null', () => {
    renderController({ material_result: null });
    expect(screen.queryByTestId('surface-type-badge')).not.toBeInTheDocument();
  });

  it('surface-type-badge shows correct surface type text', () => {
    renderController({ material_result: mockMaterial });
    expect(screen.getByTestId('surface-type-badge')).toHaveTextContent('metal');
  });
});
