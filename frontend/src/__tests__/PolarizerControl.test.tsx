import { render, screen, fireEvent } from '@testing-library/react';
import { configureStore } from '@reduxjs/toolkit';
import { Provider } from 'react-redux';
import PolarizerControl from '../components/light_test/PolarizerControl';
import lightTestReducer, {
  addLight,
  selectLight,
} from '../store/slices/lightTestSlice';
import type { LightConfig } from '../services/types';

const makeLight = (shape: LightConfig['shape'] = 'ring'): LightConfig => ({
  id: 'light-1',
  type: 'led',
  shape,
  position: { x: 0, y: 0, z: 300 },
  intensity: 80,
  color: { r: 255, g: 255, b: 255 },
  polarizer: false,
});

function makeStore() {
  return configureStore({ reducer: { light_test: lightTestReducer } });
}

const renderComponent = (store: ReturnType<typeof makeStore>) =>
  render(
    <Provider store={store}>
      <PolarizerControl />
    </Provider>,
  );

describe('PolarizerControl', () => {
  it('renders the control container', () => {
    const store = makeStore();
    renderComponent(store);
    expect(screen.getByTestId('polarizer-control')).toBeInTheDocument();
  });

  it('shows lens polarizer slider always', () => {
    const store = makeStore();
    renderComponent(store);
    expect(screen.getByTestId('lens-polarizer-slider')).toBeInTheDocument();
  });

  it('shows light polarizer checkbox for ring shape', () => {
    const store = makeStore();
    store.dispatch(addLight(makeLight('ring')));
    store.dispatch(selectLight('light-1'));
    renderComponent(store);
    expect(screen.getByTestId('light-polarizer-checkbox')).toBeInTheDocument();
  });

  it('shows spot dial for spot shape', () => {
    const store = makeStore();
    store.dispatch(addLight(makeLight('spot')));
    store.dispatch(selectLight('light-1'));
    renderComponent(store);
    expect(screen.getByTestId('light-polarizer-spot-dial')).toBeInTheDocument();
  });

  it('does not show spot dial for ring shape', () => {
    const store = makeStore();
    store.dispatch(addLight(makeLight('ring')));
    store.dispatch(selectLight('light-1'));
    renderComponent(store);
    expect(screen.queryByTestId('light-polarizer-spot-dial')).not.toBeInTheDocument();
  });

  it('dispatches updateLight when checkbox is toggled', () => {
    const store = makeStore();
    store.dispatch(addLight(makeLight('ring')));
    store.dispatch(selectLight('light-1'));
    renderComponent(store);
    fireEvent.click(screen.getByTestId('light-polarizer-checkbox'));
    const light = store.getState().light_test.lights[0];
    expect(light.polarizer_enabled).toBe(true);
  });

  it('dispatches setLensPolarizer when lens slider changes', () => {
    const store = makeStore();
    renderComponent(store);
    fireEvent.change(screen.getByTestId('lens-polarizer-slider'), { target: { value: '90' } });
    expect(store.getState().light_test.lens_polarizer_angle).toBe(90);
  });

  it('lens slider default value is 0', () => {
    const store = makeStore();
    renderComponent(store);
    const slider = screen.getByTestId('lens-polarizer-slider') as HTMLInputElement;
    expect(slider.value).toBe('0');
  });

  it('dispatches polarizer_angle when spot dial changes', () => {
    const store = makeStore();
    store.dispatch(addLight(makeLight('spot')));
    store.dispatch(selectLight('light-1'));
    renderComponent(store);
    fireEvent.change(screen.getByTestId('light-polarizer-spot-dial'), { target: { value: '90' } });
    const light = store.getState().light_test.lights[0];
    expect(light.polarizer_angle).toBe(90);
  });

  it('checkbox is not shown when no light is selected', () => {
    const store = makeStore();
    renderComponent(store);
    expect(screen.queryByTestId('light-polarizer-checkbox')).not.toBeInTheDocument();
  });
});
