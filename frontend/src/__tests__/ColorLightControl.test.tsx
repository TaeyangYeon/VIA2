import { render, screen, fireEvent } from '@testing-library/react';
import { configureStore } from '@reduxjs/toolkit';
import { Provider } from 'react-redux';
import ColorLightControl from '../components/light_test/ColorLightControl';
import lightTestReducer, {
  addLight,
  selectLight,
  setIsGrayscale,
} from '../store/slices/lightTestSlice';
import type { LightConfig } from '../services/types';

const mockLight: LightConfig = {
  id: 'light-1',
  type: 'led',
  shape: 'ring',
  position: { x: 0, y: 0, z: 300 },
  intensity: 80,
  color: { r: 200, g: 100, b: 50 },
  polarizer: false,
};

const makeStore = (extraActions: ((store: ReturnType<typeof makeBaseStore>) => void)[] = []) => {
  const store = makeBaseStore();
  for (const action of extraActions) action(store);
  return store;
};

function makeBaseStore() {
  return configureStore({ reducer: { light_test: lightTestReducer } });
}

const renderComponent = (store: ReturnType<typeof makeBaseStore>) =>
  render(
    <Provider store={store}>
      <ColorLightControl />
    </Provider>,
  );

describe('ColorLightControl', () => {
  it('renders nothing when no light is selected', () => {
    const store = makeStore();
    const { container } = renderComponent(store);
    expect(container.firstChild).toBeNull();
  });

  it('renders color controls when a light is selected', () => {
    const store = makeStore();
    store.dispatch(addLight(mockLight));
    store.dispatch(selectLight('light-1'));
    renderComponent(store);
    expect(screen.getByTestId('color-light-control')).toBeInTheDocument();
  });

  it('renders R, G, B sliders', () => {
    const store = makeStore();
    store.dispatch(addLight(mockLight));
    store.dispatch(selectLight('light-1'));
    renderComponent(store);
    expect(screen.getByTestId('color-r-slider')).toBeInTheDocument();
    expect(screen.getByTestId('color-g-slider')).toBeInTheDocument();
    expect(screen.getByTestId('color-b-slider')).toBeInTheDocument();
  });

  it('renders color preview swatch', () => {
    const store = makeStore();
    store.dispatch(addLight(mockLight));
    store.dispatch(selectLight('light-1'));
    renderComponent(store);
    expect(screen.getByTestId('color-preview-swatch')).toBeInTheDocument();
  });

  it('sliders reflect current color values', () => {
    const store = makeStore();
    store.dispatch(addLight(mockLight));
    store.dispatch(selectLight('light-1'));
    renderComponent(store);
    expect((screen.getByTestId('color-r-slider') as HTMLInputElement).value).toBe('200');
    expect((screen.getByTestId('color-g-slider') as HTMLInputElement).value).toBe('100');
    expect((screen.getByTestId('color-b-slider') as HTMLInputElement).value).toBe('50');
  });

  it('dispatches updateLight when R slider changes', () => {
    const store = makeStore();
    store.dispatch(addLight(mockLight));
    store.dispatch(selectLight('light-1'));
    renderComponent(store);
    fireEvent.change(screen.getByTestId('color-r-slider'), { target: { value: '255' } });
    const light = store.getState().light_test.lights[0];
    expect(light.color.r).toBe(255);
  });

  it('shows grayscale disabled message when image is grayscale', () => {
    const store = makeStore();
    store.dispatch(addLight(mockLight));
    store.dispatch(selectLight('light-1'));
    store.dispatch(setIsGrayscale(true));
    renderComponent(store);
    expect(screen.getByTestId('color-disabled-message')).toBeInTheDocument();
  });

  it('does not show disabled message when image is color', () => {
    const store = makeStore();
    store.dispatch(addLight(mockLight));
    store.dispatch(selectLight('light-1'));
    store.dispatch(setIsGrayscale(false));
    renderComponent(store);
    expect(screen.queryByTestId('color-disabled-message')).not.toBeInTheDocument();
  });

  it('disables sliders when image is grayscale', () => {
    const store = makeStore();
    store.dispatch(addLight(mockLight));
    store.dispatch(selectLight('light-1'));
    store.dispatch(setIsGrayscale(true));
    renderComponent(store);
    expect(screen.getByTestId('color-r-slider')).toBeDisabled();
    expect(screen.getByTestId('color-g-slider')).toBeDisabled();
    expect(screen.getByTestId('color-b-slider')).toBeDisabled();
  });
});
