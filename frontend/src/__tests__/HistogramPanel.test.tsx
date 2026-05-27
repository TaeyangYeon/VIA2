import { render, screen } from '@testing-library/react';
import { configureStore } from '@reduxjs/toolkit';
import { Provider } from 'react-redux';
import HistogramPanel from '../components/light_test/HistogramPanel';
import lightTestReducer, {
  setRenderedResult,
  setIsGrayscale,
} from '../store/slices/lightTestSlice';

const mockCtx = {
  clearRect: jest.fn(),
  drawImage: jest.fn(),
  fillRect: jest.fn(),
  getImageData: jest.fn(() => ({
    data: new Uint8ClampedArray([100, 100, 100, 255, 200, 50, 30, 255]),
    width: 2,
    height: 1,
  })),
  strokeStyle: '',
  lineWidth: 1,
  globalAlpha: 1,
  beginPath: jest.fn(),
  moveTo: jest.fn(),
  lineTo: jest.fn(),
  stroke: jest.fn(),
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

function makeStore() {
  return configureStore({ reducer: { light_test: lightTestReducer } });
}

const renderComponent = (store: ReturnType<typeof makeStore>) =>
  render(
    <Provider store={store}>
      <HistogramPanel />
    </Provider>,
  );

describe('HistogramPanel', () => {
  it('renders the histogram panel container', () => {
    const store = makeStore();
    renderComponent(store);
    expect(screen.getByTestId('histogram-panel')).toBeInTheDocument();
  });

  it('renders the histogram canvas', () => {
    const store = makeStore();
    renderComponent(store);
    expect(screen.getByTestId('histogram-canvas')).toBeInTheDocument();
  });

  it('shows "No render yet" when there is no rendered result', () => {
    const store = makeStore();
    renderComponent(store);
    expect(screen.getByText('No render yet')).toBeInTheDocument();
  });

  it('shows R, G, B channel labels for color image', () => {
    const store = makeStore();
    store.dispatch(setRenderedResult('fakeBase64=='));
    store.dispatch(setIsGrayscale(false));
    renderComponent(store);
    expect(screen.getByTestId('histogram-channel-r')).toBeInTheDocument();
    expect(screen.getByTestId('histogram-channel-g')).toBeInTheDocument();
    expect(screen.getByTestId('histogram-channel-b')).toBeInTheDocument();
  });

  it('shows L channel label for grayscale image', () => {
    const store = makeStore();
    store.dispatch(setRenderedResult('fakeBase64=='));
    store.dispatch(setIsGrayscale(true));
    renderComponent(store);
    expect(screen.getByTestId('histogram-channel-l')).toBeInTheDocument();
    expect(screen.queryByTestId('histogram-channel-r')).not.toBeInTheDocument();
  });

  it('does not show "No render yet" when result is present', () => {
    const store = makeStore();
    store.dispatch(setRenderedResult('fakeBase64=='));
    renderComponent(store);
    expect(screen.queryByText('No render yet')).not.toBeInTheDocument();
  });
});
