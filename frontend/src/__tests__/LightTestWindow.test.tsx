import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import lightTestReducer from '../store/slices/lightTestSlice';
import LightTestWindow from '../components/light_test/LightTestWindow';
import * as api from '../services/api';
import type { ImageMetadata } from '../services/types';

jest.mock('../services/api');
const mockedApi = api as jest.Mocked<typeof api>;

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

const makeStore = () =>
  configureStore({ reducer: { light_test: lightTestReducer } });

const renderWithStore = (ui: React.ReactElement, storeOverride?: ReturnType<typeof makeStore>) => {
  const s = storeOverride ?? makeStore();
  return { ...render(<Provider store={s}>{ui}</Provider>), store: s };
};

const mockImage: ImageMetadata = {
  id: 'lt-123',
  original_filename: 'test_image.png',
  label: '',
  index: 0,
  file_size: 10240,
  upload_timestamp: '2026-01-01T00:00:00Z',
  file_path: '/images/test_image.png',
  group: 'light_test',
};

describe('LightTestWindow', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedApi.uploadImage.mockResolvedValue(mockImage);
  });

  it('renders without crashing', () => {
    const { container } = renderWithStore(<LightTestWindow />);
    expect(container).toBeTruthy();
  });

  it('has data-testid="light-test-window"', () => {
    renderWithStore(<LightTestWindow />);
    expect(screen.getByTestId('light-test-window')).toBeInTheDocument();
  });

  it('renders header with data-testid="light-test-header"', () => {
    renderWithStore(<LightTestWindow />);
    expect(screen.getByTestId('light-test-header')).toBeInTheDocument();
  });

  it('shows VIA2 in header title', () => {
    renderWithStore(<LightTestWindow />);
    expect(screen.getByTestId('light-test-header')).toHaveTextContent('VIA2');
  });

  it('shows "Light Test" in header title', () => {
    renderWithStore(<LightTestWindow />);
    expect(screen.getByTestId('light-test-header')).toHaveTextContent('Light Test');
  });

  it('renders drop zone when no image uploaded', () => {
    renderWithStore(<LightTestWindow />);
    expect(screen.getByTestId('lt-drop-zone')).toBeInTheDocument();
  });

  it('renders empty state instructions when no image', () => {
    renderWithStore(<LightTestWindow />);
    expect(screen.getByTestId('lt-empty-state')).toBeInTheDocument();
  });

  it('renders file input for image upload', () => {
    renderWithStore(<LightTestWindow />);
    expect(screen.getByTestId('lt-file-input')).toBeInTheDocument();
  });

  it('renders browse button initially', () => {
    renderWithStore(<LightTestWindow />);
    expect(screen.getByTestId('lt-browse-btn')).toBeInTheDocument();
  });

  it('calls api.uploadImage when file is selected', async () => {
    renderWithStore(<LightTestWindow />);
    const file = new File(['test'], 'test.png', { type: 'image/png' });
    const fileInput = screen.getByTestId('lt-file-input');
    await act(async () => {
      fireEvent.change(fileInput, { target: { files: [file] } });
    });
    await waitFor(() => {
      expect(mockedApi.uploadImage).toHaveBeenCalledWith(file);
    });
  });

  it('dispatches setLightTestImage after successful upload', async () => {
    const { store } = renderWithStore(<LightTestWindow />);
    const file = new File(['test'], 'test.png', { type: 'image/png' });
    const fileInput = screen.getByTestId('lt-file-input');
    await act(async () => {
      fireEvent.change(fileInput, { target: { files: [file] } });
    });
    await waitFor(() => {
      expect((store.getState() as { light_test: { image: ImageMetadata | null } }).light_test.image).toEqual(mockImage);
    });
  });

  it('shows image thumbnail after successful upload', async () => {
    renderWithStore(<LightTestWindow />);
    const file = new File(['test'], 'test.png', { type: 'image/png' });
    await act(async () => {
      fireEvent.change(screen.getByTestId('lt-file-input'), { target: { files: [file] } });
    });
    await waitFor(() => {
      expect(screen.getByTestId('lt-image-thumbnail')).toBeInTheDocument();
    });
  });

  it('shows original_filename in thumbnail after upload', async () => {
    renderWithStore(<LightTestWindow />);
    const file = new File(['test'], 'test.png', { type: 'image/png' });
    await act(async () => {
      fireEvent.change(screen.getByTestId('lt-file-input'), { target: { files: [file] } });
    });
    await waitFor(() => {
      expect(screen.getByText('test_image.png')).toBeInTheDocument();
    });
  });

  it('renders remove button after upload', async () => {
    renderWithStore(<LightTestWindow />);
    const file = new File(['test'], 'test.png', { type: 'image/png' });
    await act(async () => {
      fireEvent.change(screen.getByTestId('lt-file-input'), { target: { files: [file] } });
    });
    await waitFor(() => {
      expect(screen.getByTestId('lt-remove-btn')).toBeInTheDocument();
    });
  });

  it('shows DualViewLayout after image upload', async () => {
    renderWithStore(<LightTestWindow />);
    const file = new File(['test'], 'test.png', { type: 'image/png' });
    await act(async () => {
      fireEvent.change(screen.getByTestId('lt-file-input'), { target: { files: [file] } });
    });
    await waitFor(() => {
      expect(screen.getByTestId('dual-view-layout')).toBeInTheDocument();
    });
  });

  it('removes image when remove button is clicked', async () => {
    const { store } = renderWithStore(<LightTestWindow />);
    const file = new File(['test'], 'test.png', { type: 'image/png' });
    await act(async () => {
      fireEvent.change(screen.getByTestId('lt-file-input'), { target: { files: [file] } });
    });
    await waitFor(() => {
      expect(screen.getByTestId('lt-remove-btn')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId('lt-remove-btn'));
    await waitFor(() => {
      expect((store.getState() as { light_test: { image: ImageMetadata | null } }).light_test.image).toBeNull();
    });
  });

  it('shows lt-loading-state during upload', async () => {
    let resolveUpload!: (value: ImageMetadata) => void;
    mockedApi.uploadImage.mockImplementation(
      () => new Promise(resolve => { resolveUpload = resolve; }),
    );
    renderWithStore(<LightTestWindow />);
    const file = new File(['test'], 'loading.png', { type: 'image/png' });
    act(() => {
      fireEvent.change(screen.getByTestId('lt-file-input'), { target: { files: [file] } });
    });
    await waitFor(() => {
      expect(screen.getByTestId('lt-loading-state')).toBeInTheDocument();
    });
    await act(async () => { resolveUpload(mockImage); });
  });

  it('shows lt-error-state when upload fails', async () => {
    mockedApi.uploadImage.mockRejectedValue(new Error('Upload failed'));
    renderWithStore(<LightTestWindow />);
    const file = new File(['test'], 'fail.png', { type: 'image/png' });
    await act(async () => {
      fireEvent.change(screen.getByTestId('lt-file-input'), { target: { files: [file] } });
    });
    await waitFor(() => {
      expect(screen.getByTestId('lt-error-state')).toBeInTheDocument();
    });
  });

  it('does not require OK_/NG_ prefix in filename', async () => {
    renderWithStore(<LightTestWindow />);
    const file = new File(['test'], 'arbitrary_name.jpg', { type: 'image/jpeg' });
    await act(async () => {
      fireEvent.change(screen.getByTestId('lt-file-input'), { target: { files: [file] } });
    });
    await waitFor(() => {
      expect(mockedApi.uploadImage).toHaveBeenCalledWith(file);
    });
  });

  it('does not show DualViewLayout when no image is loaded', () => {
    renderWithStore(<LightTestWindow />);
    expect(screen.queryByTestId('dual-view-layout')).not.toBeInTheDocument();
  });

  it('hides drop zone after successful upload', async () => {
    renderWithStore(<LightTestWindow />);
    const file = new File(['test'], 'test.png', { type: 'image/png' });
    await act(async () => {
      fireEvent.change(screen.getByTestId('lt-file-input'), { target: { files: [file] } });
    });
    await waitFor(() => {
      expect(screen.queryByTestId('lt-drop-zone')).not.toBeInTheDocument();
    });
  });
});
