import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import imagesReducer from '../store/slices/imagesSlice';
import InputPanel from '../components/panels/InputPanel';
import * as api from '../services/api';
import type { ImageMetadata } from '../services/types';

jest.mock('../services/api');
const mockedApi = api as jest.Mocked<typeof api>;

const makeStore = () =>
  configureStore({ reducer: { images: imagesReducer } });

const renderWithStore = (ui: React.ReactElement, storeOverride?: ReturnType<typeof makeStore>) => {
  const s = storeOverride ?? makeStore();
  return { ...render(<Provider store={s}>{ui}</Provider>), store: s };
};

const mockImage: ImageMetadata = {
  id: 'abc-123',
  original_filename: 'OK_1.png',
  label: 'OK',
  index: 1,
  file_size: 10240,
  upload_timestamp: '2026-01-01T00:00:00Z',
  file_path: '/images/OK_1.png',
  group: 'analysis',
};

describe('InputPanel component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedApi.getImages.mockResolvedValue([]);
    mockedApi.uploadImage.mockResolvedValue(mockImage);
    mockedApi.deleteImage.mockResolvedValue({ message: 'deleted' });
    mockedApi.clearAllImages.mockResolvedValue({ message: 'cleared' });
  });

  it('renders without crashing', () => {
    const { container } = renderWithStore(<InputPanel />);
    expect(container).toBeTruthy();
  });

  it('has data-testid="input-panel"', () => {
    renderWithStore(<InputPanel />);
    expect(screen.getByTestId('input-panel')).toBeInTheDocument();
  });

  it('shows empty state when no images', async () => {
    renderWithStore(<InputPanel />);
    await waitFor(() => {
      expect(screen.getByTestId('empty-state')).toBeInTheDocument();
    });
  });

  it('renders drag & drop zone', () => {
    renderWithStore(<InputPanel />);
    expect(screen.getByTestId('drop-zone')).toBeInTheDocument();
  });

  it('renders file input (hidden)', () => {
    renderWithStore(<InputPanel />);
    const input = screen.getByTestId('file-input') as HTMLInputElement;
    expect(input).toBeInTheDocument();
    expect(input.type).toBe('file');
  });

  it('file input accepts image types', () => {
    renderWithStore(<InputPanel />);
    const input = screen.getByTestId('file-input') as HTMLInputElement;
    expect(input.accept).toContain('image/');
  });

  it('loads images from API on mount', async () => {
    mockedApi.getImages.mockResolvedValue([mockImage]);
    renderWithStore(<InputPanel />);
    await waitFor(() => {
      expect(mockedApi.getImages).toHaveBeenCalled();
    });
  });

  describe('filename validation', () => {
    const validNames = ['OK_1.png', 'NG_3.jpg', 'ok_2.PNG', 'ng_1.bmp', 'OK_10.jpeg', 'NG_99.tiff'];
    const invalidNames = ['test.png', 'OK.png', 'NG_0.png', 'OK_abc.png', 'image.jpg', 'OK_-1.png'];

    validNames.forEach(name => {
      it(`accepts valid filename: ${name}`, async () => {
        renderWithStore(<InputPanel />);
        const input = screen.getByTestId('file-input') as HTMLInputElement;
        const file = new File(['data'], name, { type: 'image/png' });
        Object.defineProperty(input, 'files', { value: [file], configurable: true });
        await act(async () => {
          fireEvent.change(input);
        });
        await waitFor(() => {
          expect(screen.queryByTestId('validation-error')).not.toBeInTheDocument();
        });
      });
    });

    invalidNames.forEach(name => {
      it(`rejects invalid filename: ${name}`, async () => {
        renderWithStore(<InputPanel />);
        const input = screen.getByTestId('file-input') as HTMLInputElement;
        const file = new File(['data'], name, { type: 'image/png' });
        Object.defineProperty(input, 'files', { value: [file], configurable: true });
        await act(async () => {
          fireEvent.change(input);
        });
        await waitFor(() => {
          expect(screen.getByTestId('validation-error')).toBeInTheDocument();
        });
      });
    });
  });

  describe('image list', () => {
    it('shows thumbnails after images loaded', async () => {
      mockedApi.getImages.mockResolvedValue([mockImage]);
      renderWithStore(<InputPanel />);
      await waitFor(() => {
        expect(screen.getByTestId(`thumbnail-${mockImage.id}`)).toBeInTheDocument();
      });
    });

    it('shows filename in thumbnail', async () => {
      mockedApi.getImages.mockResolvedValue([mockImage]);
      renderWithStore(<InputPanel />);
      await waitFor(() => {
        expect(screen.getByText('OK_1.png')).toBeInTheDocument();
      });
    });

    it('shows label (OK/NG) in thumbnail', async () => {
      mockedApi.getImages.mockResolvedValue([mockImage]);
      renderWithStore(<InputPanel />);
      await waitFor(() => {
        expect(screen.getByTestId(`label-${mockImage.id}`)).toBeInTheDocument();
      });
    });

    it('shows delete button on each thumbnail', async () => {
      mockedApi.getImages.mockResolvedValue([mockImage]);
      renderWithStore(<InputPanel />);
      await waitFor(() => {
        expect(screen.getByTestId(`delete-${mockImage.id}`)).toBeInTheDocument();
      });
    });

    it('calls deleteImage API when delete button clicked', async () => {
      mockedApi.getImages.mockResolvedValue([mockImage]);
      renderWithStore(<InputPanel />);
      await waitFor(() => screen.getByTestId(`delete-${mockImage.id}`));
      await act(async () => {
        fireEvent.click(screen.getByTestId(`delete-${mockImage.id}`));
      });
      await waitFor(() => {
        expect(mockedApi.deleteImage).toHaveBeenCalledWith(mockImage.id);
      });
    });
  });

  describe('image count summary', () => {
    it('shows OK and NG counts', async () => {
      const ngImage: ImageMetadata = { ...mockImage, id: 'ng-1', original_filename: 'NG_1.png', label: 'NG' };
      mockedApi.getImages.mockResolvedValue([mockImage, ngImage]);
      renderWithStore(<InputPanel />);
      await waitFor(() => {
        expect(screen.getByTestId('count-summary')).toBeInTheDocument();
      });
    });
  });

  describe('Clear All button', () => {
    it('renders clear all button', async () => {
      mockedApi.getImages.mockResolvedValue([mockImage]);
      renderWithStore(<InputPanel />);
      await waitFor(() => {
        expect(screen.getByTestId('clear-all-btn')).toBeInTheDocument();
      });
    });

    it('calls clearAllImages when clicked', async () => {
      mockedApi.getImages.mockResolvedValue([mockImage]);
      renderWithStore(<InputPanel />);
      await waitFor(() => screen.getByTestId('clear-all-btn'));
      await act(async () => {
        fireEvent.click(screen.getByTestId('clear-all-btn'));
      });
      await waitFor(() => {
        expect(mockedApi.clearAllImages).toHaveBeenCalled();
      });
    });
  });

  describe('drag & drop', () => {
    it('adds drag-over style on dragenter', () => {
      renderWithStore(<InputPanel />);
      const zone = screen.getByTestId('drop-zone');
      fireEvent.dragEnter(zone);
      expect(zone).toHaveAttribute('data-dragging', 'true');
    });

    it('removes drag-over style on dragleave', () => {
      renderWithStore(<InputPanel />);
      const zone = screen.getByTestId('drop-zone');
      fireEvent.dragEnter(zone);
      fireEvent.dragLeave(zone);
      expect(zone).toHaveAttribute('data-dragging', 'false');
    });

    it('removes drag-over style on drop', async () => {
      renderWithStore(<InputPanel />);
      const zone = screen.getByTestId('drop-zone');
      fireEvent.dragEnter(zone);
      const file = new File(['data'], 'OK_1.png', { type: 'image/png' });
      await act(async () => {
        fireEvent.drop(zone, { dataTransfer: { files: [file] } });
      });
      expect(zone).toHaveAttribute('data-dragging', 'false');
    });
  });

  describe('loading state', () => {
    it('shows loading indicator during upload', async () => {
      let resolve: (v: ImageMetadata) => void;
      mockedApi.uploadImage.mockReturnValue(new Promise(r => { resolve = r; }));
      renderWithStore(<InputPanel />);
      const input = screen.getByTestId('file-input') as HTMLInputElement;
      const file = new File(['data'], 'OK_1.png', { type: 'image/png' });
      Object.defineProperty(input, 'files', { value: [file], configurable: true });
      await act(async () => {
        fireEvent.change(input);
      });
      expect(screen.getByTestId('upload-loading')).toBeInTheDocument();
      await act(async () => { resolve!(mockImage); });
    });
  });

  describe('error state', () => {
    it('shows error when upload fails', async () => {
      mockedApi.uploadImage.mockRejectedValue(new Error('Upload failed'));
      renderWithStore(<InputPanel />);
      const input = screen.getByTestId('file-input') as HTMLInputElement;
      const file = new File(['data'], 'OK_1.png', { type: 'image/png' });
      Object.defineProperty(input, 'files', { value: [file], configurable: true });
      await act(async () => {
        fireEvent.change(input);
      });
      await waitFor(() => {
        expect(screen.getByTestId('upload-error')).toBeInTheDocument();
      });
    });
  });
});
