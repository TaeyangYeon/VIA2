import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import imagesReducer from '../store/slices/imagesSlice';
import roiReducer from '../store/slices/roiSlice';
import ROICanvas from '../components/ROICanvas';
import * as api from '../services/api';
import type { ImageMetadata, ROICoordinates } from '../services/types';

// ── API mock ──────────────────────────────────────────────────────────────────
jest.mock('../services/api');
const mockedApi = api as jest.Mocked<typeof api>;

// ── Canvas context mock ───────────────────────────────────────────────────────
const mockCtx = {
  clearRect: jest.fn(),
  drawImage: jest.fn(),
  fillRect: jest.fn(),
  strokeRect: jest.fn(),
  setLineDash: jest.fn(),
  save: jest.fn(),
  restore: jest.fn(),
  beginPath: jest.fn(),
  rect: jest.fn(),
  fill: jest.fn(),
  stroke: jest.fn(),
  fillStyle: '',
  strokeStyle: '',
  lineWidth: 0,
  globalAlpha: 1,
  globalCompositeOperation: 'source-over',
};

// ── Controllable MockImage ────────────────────────────────────────────────────
let currentMockImage: {
  onload: (() => void) | null;
  onerror: (() => void) | null;
  naturalWidth: number;
  naturalHeight: number;
  crossOrigin: string;
  src: string;
} | null = null;

class MockImage {
  onload: (() => void) | null = null;
  onerror: (() => void) | null = null;
  naturalWidth = 800;
  naturalHeight = 600;
  crossOrigin = '';
  src = '';

  constructor() {
    // eslint-disable-next-line @typescript-eslint/no-this-alias
    currentMockImage = this;
  }
}

// ── Store factory ─────────────────────────────────────────────────────────────
const makeStore = (images: ImageMetadata[] = [], roi: ROICoordinates | null = null) =>
  configureStore({
    reducer: { images: imagesReducer, roi: roiReducer },
    preloadedState: {
      images: { analysis: images, test: [] as ImageMetadata[] },
      roi,
    },
  });

const renderWithStore = (images: ImageMetadata[] = [], roi: ROICoordinates | null = null) => {
  const store = makeStore(images, roi);
  const utils = render(
    <Provider store={store}>
      <ROICanvas />
    </Provider>,
  );
  return { ...utils, store };
};

// ── Test data ─────────────────────────────────────────────────────────────────
const mockImage: ImageMetadata = {
  id: 'img-001',
  original_filename: 'OK_1.png',
  label: 'ok',
  index: 0,
  file_size: 12345,
  upload_timestamp: '2026-01-01T00:00:00Z',
  file_path: '/uploads/OK_1.png',
  group: 'analysis',
};

const mockRoi: ROICoordinates = { x1: 10, y1: 20, x2: 300, y2: 400 };

// ── Setup / teardown ──────────────────────────────────────────────────────────
beforeEach(() => {
  currentMockImage = null;
  jest.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(
    mockCtx as unknown as CanvasRenderingContext2D,
  );
  global.Image = MockImage as unknown as typeof Image;
  jest.clearAllMocks();
  mockedApi.setRoi.mockResolvedValue(mockRoi);
  mockedApi.clearRoi.mockResolvedValue({ message: 'cleared' });
});

afterEach(() => {
  jest.restoreAllMocks();
});

// ── Empty state ───────────────────────────────────────────────────────────────
describe('ROICanvas — empty state', () => {
  it('renders without crashing with no images', () => {
    const { container } = renderWithStore();
    expect(container).toBeTruthy();
  });

  it('shows empty state UI when no analysis images', () => {
    renderWithStore();
    expect(screen.getByTestId('roi-empty-state')).toBeInTheDocument();
  });

  it('empty state contains prompt to upload images', () => {
    renderWithStore();
    expect(screen.getByTestId('roi-empty-state')).toHaveTextContent(/upload/i);
  });

  it('does not render canvas in empty state', () => {
    renderWithStore();
    expect(screen.queryByTestId('roi-canvas')).not.toBeInTheDocument();
  });
});

// ── Loading state ─────────────────────────────────────────────────────────────
describe('ROICanvas — loading state', () => {
  it('shows loading indicator when image is loading', async () => {
    renderWithStore([mockImage]);
    await waitFor(() => {
      expect(screen.getByTestId('roi-loading')).toBeInTheDocument();
    });
  });

  it('does not show canvas while loading', () => {
    renderWithStore([mockImage]);
    expect(screen.queryByTestId('roi-canvas')).not.toBeInTheDocument();
  });
});

// ── Loaded state ──────────────────────────────────────────────────────────────
describe('ROICanvas — loaded state', () => {
  const renderAndLoad = async (images = [mockImage], roi: ROICoordinates | null = null) => {
    const result = renderWithStore(images, roi);
    await act(async () => {
      currentMockImage?.onload?.();
    });
    return result;
  };

  it('renders canvas when image loads', async () => {
    await renderAndLoad();
    await waitFor(() => {
      expect(screen.getByTestId('roi-canvas')).toBeInTheDocument();
    });
  });

  it('hides loading indicator after image loads', async () => {
    await renderAndLoad();
    await waitFor(() => {
      expect(screen.queryByTestId('roi-loading')).not.toBeInTheDocument();
    });
  });

  it('renders save button', async () => {
    await renderAndLoad();
    await waitFor(() => {
      expect(screen.getByTestId('roi-save-btn')).toBeInTheDocument();
    });
  });

  it('renders delete button', async () => {
    await renderAndLoad();
    await waitFor(() => {
      expect(screen.getByTestId('roi-delete-btn')).toBeInTheDocument();
    });
  });

  it('calls getContext on the canvas element after load', async () => {
    await renderAndLoad();
    await waitFor(() => {
      expect(HTMLCanvasElement.prototype.getContext).toHaveBeenCalled();
    });
  });

  it('shows roi-canvas with correct data-testid', async () => {
    await renderAndLoad();
    await waitFor(() => {
      const canvas = screen.getByTestId('roi-canvas');
      expect(canvas.tagName).toBe('CANVAS');
    });
  });
});

// ── Error state ───────────────────────────────────────────────────────────────
describe('ROICanvas — error state', () => {
  it('shows error state when image fails to load', async () => {
    renderWithStore([mockImage]);
    await act(async () => {
      currentMockImage?.onerror?.();
    });
    await waitFor(() => {
      expect(screen.getByTestId('roi-error')).toBeInTheDocument();
    });
  });

  it('error state has helpful message', async () => {
    renderWithStore([mockImage]);
    await act(async () => {
      currentMockImage?.onerror?.();
    });
    await waitFor(() => {
      expect(screen.getByTestId('roi-error')).toHaveTextContent(/load|error|fail/i);
    });
  });

  it('does not show canvas in error state', async () => {
    renderWithStore([mockImage]);
    await act(async () => {
      currentMockImage?.onerror?.();
    });
    await waitFor(() => {
      expect(screen.queryByTestId('roi-canvas')).not.toBeInTheDocument();
    });
  });
});

// ── ROI coordinates panel ─────────────────────────────────────────────────────
describe('ROICanvas — ROI coordinates panel', () => {
  const renderAndLoad = async (roi: ROICoordinates | null = null) => {
    const result = renderWithStore([mockImage], roi);
    await act(async () => {
      currentMockImage?.onload?.();
    });
    return result;
  };

  it('shows ROI info panel when roi is set in store', async () => {
    await renderAndLoad(mockRoi);
    await waitFor(() => {
      expect(screen.getByTestId('roi-coords-panel')).toBeInTheDocument();
    });
  });

  it('shows x1 input with stored value', async () => {
    await renderAndLoad(mockRoi);
    await waitFor(() => {
      const input = screen.getByTestId('roi-x1-input') as HTMLInputElement;
      expect(Number(input.value)).toBe(mockRoi.x1);
    });
  });

  it('shows y1 input with stored value', async () => {
    await renderAndLoad(mockRoi);
    await waitFor(() => {
      const input = screen.getByTestId('roi-y1-input') as HTMLInputElement;
      expect(Number(input.value)).toBe(mockRoi.y1);
    });
  });

  it('shows x2 input with stored value', async () => {
    await renderAndLoad(mockRoi);
    await waitFor(() => {
      const input = screen.getByTestId('roi-x2-input') as HTMLInputElement;
      expect(Number(input.value)).toBe(mockRoi.x2);
    });
  });

  it('shows y2 input with stored value', async () => {
    await renderAndLoad(mockRoi);
    await waitFor(() => {
      const input = screen.getByTestId('roi-y2-input') as HTMLInputElement;
      expect(Number(input.value)).toBe(mockRoi.y2);
    });
  });
});

// ── Save button ───────────────────────────────────────────────────────────────
describe('ROICanvas — save button', () => {
  const renderLoadAndSetRoi = async () => {
    const result = renderWithStore([mockImage], mockRoi);
    await act(async () => {
      currentMockImage?.onload?.();
    });
    await waitFor(() => screen.getByTestId('roi-save-btn'));
    return result;
  };

  it('calls api.setRoi when save is clicked', async () => {
    await renderLoadAndSetRoi();
    await act(async () => {
      fireEvent.click(screen.getByTestId('roi-save-btn'));
    });
    await waitFor(() => {
      expect(mockedApi.setRoi).toHaveBeenCalledWith(mockRoi);
    });
  });

  it('dispatches setRoi action to redux store', async () => {
    const { store } = await renderLoadAndSetRoi();
    await act(async () => {
      fireEvent.click(screen.getByTestId('roi-save-btn'));
    });
    await waitFor(() => {
      expect(store.getState().roi).toEqual(mockRoi);
    });
  });
});

// ── Delete button ─────────────────────────────────────────────────────────────
describe('ROICanvas — delete button', () => {
  const renderLoadAndSetRoi = async () => {
    const result = renderWithStore([mockImage], mockRoi);
    await act(async () => {
      currentMockImage?.onload?.();
    });
    await waitFor(() => screen.getByTestId('roi-delete-btn'));
    return result;
  };

  it('calls api.clearRoi when delete is clicked', async () => {
    await renderLoadAndSetRoi();
    await act(async () => {
      fireEvent.click(screen.getByTestId('roi-delete-btn'));
    });
    await waitFor(() => {
      expect(mockedApi.clearRoi).toHaveBeenCalled();
    });
  });

  it('dispatches clearRoi action to redux store', async () => {
    const { store } = await renderLoadAndSetRoi();
    await act(async () => {
      fireEvent.click(screen.getByTestId('roi-delete-btn'));
    });
    await waitFor(() => {
      expect(store.getState().roi).toBeNull();
    });
  });

  it('hides coordinates panel after delete', async () => {
    await renderLoadAndSetRoi();
    await act(async () => {
      fireEvent.click(screen.getByTestId('roi-delete-btn'));
    });
    await waitFor(() => {
      expect(screen.queryByTestId('roi-coords-panel')).not.toBeInTheDocument();
    });
  });
});

// ── Manual coordinate input ───────────────────────────────────────────────────
describe('ROICanvas — manual coordinate input', () => {
  it('updates x1 when input changes', async () => {
    renderWithStore([mockImage], mockRoi);
    await act(async () => { currentMockImage?.onload?.(); });
    await waitFor(() => screen.getByTestId('roi-x1-input'));

    await act(async () => {
      fireEvent.change(screen.getByTestId('roi-x1-input'), { target: { value: '50' } });
    });

    await waitFor(() => {
      const input = screen.getByTestId('roi-x1-input') as HTMLInputElement;
      expect(Number(input.value)).toBe(50);
    });
  });

  it('updates y2 when input changes', async () => {
    renderWithStore([mockImage], mockRoi);
    await act(async () => { currentMockImage?.onload?.(); });
    await waitFor(() => screen.getByTestId('roi-y2-input'));

    await act(async () => {
      fireEvent.change(screen.getByTestId('roi-y2-input'), { target: { value: '450' } });
    });

    await waitFor(() => {
      const input = screen.getByTestId('roi-y2-input') as HTMLInputElement;
      expect(Number(input.value)).toBe(450);
    });
  });
});

// ── Image URL ─────────────────────────────────────────────────────────────────
describe('ROICanvas — image URL construction', () => {
  it('uses the first analysis image ID to construct URL', async () => {
    renderWithStore([mockImage]);
    await waitFor(() => {
      expect(currentMockImage?.src).toContain(mockImage.id);
    });
  });

  it('URL points to backend image file endpoint', async () => {
    renderWithStore([mockImage]);
    await waitFor(() => {
      expect(currentMockImage?.src).toMatch(/http:\/\/localhost:8000/);
    });
  });
});

// ── Layout integration ────────────────────────────────────────────────────────
describe('ROICanvas — layout', () => {
  it('has a data-testid="roi-panel" wrapper', () => {
    renderWithStore();
    expect(screen.getByTestId('roi-panel')).toBeInTheDocument();
  });
});
