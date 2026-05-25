import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import configReducer from '../store/slices/configSlice';
import ConfigPanel from '../components/panels/ConfigPanel';
import * as api from '../services/api';
import type { InspectionConfig, ConfigSaveResponse } from '../services/types';

jest.mock('../services/api');
const mockedApi = api as jest.Mocked<typeof api>;

const defaultConfig: InspectionConfig = {
  mode: 'inspection',
  max_iteration: 3,
  success_criteria: {
    accuracy: null,
    fp_rate: null,
    fn_rate: null,
    coord_error: null,
  },
};

const defaultSaveResponse: ConfigSaveResponse = {
  ...defaultConfig,
  warnings: [],
};

const makeStore = (preloaded?: Partial<InspectionConfig>) =>
  configureStore({
    reducer: { config: configReducer },
    preloadedState: preloaded ? { config: { ...defaultConfig, ...preloaded } } : undefined,
  });

const renderWithStore = (ui: React.ReactElement, store = makeStore()) =>
  ({ ...render(<Provider store={store}>{ui}</Provider>), store });

describe('ConfigPanel', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedApi.saveConfig.mockResolvedValue(defaultSaveResponse);
  });

  it('renders without crashing', () => {
    const { container } = renderWithStore(<ConfigPanel />);
    expect(container).toBeTruthy();
  });

  it('has data-testid="config-panel"', () => {
    renderWithStore(<ConfigPanel />);
    expect(screen.getByTestId('config-panel')).toBeInTheDocument();
  });

  it('shows inspection mode radio selected by default', () => {
    renderWithStore(<ConfigPanel />);
    const radio = screen.getByTestId('mode-inspection') as HTMLInputElement;
    expect(radio.checked).toBe(true);
  });

  it('shows align mode radio', () => {
    renderWithStore(<ConfigPanel />);
    expect(screen.getByTestId('mode-align')).toBeInTheDocument();
  });

  it('shows inspection criteria fields in inspection mode', () => {
    renderWithStore(<ConfigPanel />);
    expect(screen.getByTestId('accuracy-input')).toBeInTheDocument();
    expect(screen.getByTestId('fp-rate-input')).toBeInTheDocument();
    expect(screen.getByTestId('fn-rate-input')).toBeInTheDocument();
  });

  it('hides coord_error input in inspection mode', () => {
    renderWithStore(<ConfigPanel />);
    expect(screen.queryByTestId('coord-error-input')).not.toBeInTheDocument();
  });

  it('shows coord_error input in align mode', () => {
    renderWithStore(<ConfigPanel />);
    fireEvent.click(screen.getByTestId('mode-align'));
    expect(screen.getByTestId('coord-error-input')).toBeInTheDocument();
  });

  it('hides inspection criteria inputs in align mode', () => {
    renderWithStore(<ConfigPanel />);
    fireEvent.click(screen.getByTestId('mode-align'));
    expect(screen.queryByTestId('accuracy-input')).not.toBeInTheDocument();
    expect(screen.queryByTestId('fp-rate-input')).not.toBeInTheDocument();
    expect(screen.queryByTestId('fn-rate-input')).not.toBeInTheDocument();
  });

  it('has max_iteration input', () => {
    renderWithStore(<ConfigPanel />);
    expect(screen.getByTestId('max-iteration-input')).toBeInTheDocument();
  });

  it('max_iteration input defaults to 3', () => {
    renderWithStore(<ConfigPanel />);
    const input = screen.getByTestId('max-iteration-input') as HTMLInputElement;
    expect(input.value).toBe('3');
  });

  it('has save button', () => {
    renderWithStore(<ConfigPanel />);
    expect(screen.getByTestId('save-btn')).toBeInTheDocument();
  });

  it('calls saveConfig on save', async () => {
    renderWithStore(<ConfigPanel />);
    await act(async () => {
      fireEvent.click(screen.getByTestId('save-btn'));
    });
    await waitFor(() => {
      expect(mockedApi.saveConfig).toHaveBeenCalled();
    });
  });

  it('dispatches setConfig after successful save', async () => {
    const updatedResponse: ConfigSaveResponse = {
      mode: 'inspection',
      max_iteration: 3,
      success_criteria: { accuracy: 0.95, fp_rate: null, fn_rate: null, coord_error: null },
      warnings: [],
    };
    mockedApi.saveConfig.mockResolvedValue(updatedResponse);
    const store = makeStore();
    renderWithStore(<ConfigPanel />, store);
    await act(async () => {
      fireEvent.click(screen.getByTestId('save-btn'));
    });
    await waitFor(() => {
      expect(store.getState().config.success_criteria.accuracy).toBe(0.95);
    });
  });

  it('shows save-success after successful save', async () => {
    renderWithStore(<ConfigPanel />);
    await act(async () => {
      fireEvent.click(screen.getByTestId('save-btn'));
    });
    await waitFor(() => {
      expect(screen.getByTestId('save-success')).toBeInTheDocument();
    });
  });

  it('shows save-error when save fails', async () => {
    mockedApi.saveConfig.mockRejectedValue(new Error('Network error'));
    renderWithStore(<ConfigPanel />);
    await act(async () => {
      fireEvent.click(screen.getByTestId('save-btn'));
    });
    await waitFor(() => {
      expect(screen.getByTestId('save-error')).toBeInTheDocument();
    });
  });

  it('shows save-loading while saving', async () => {
    let resolve: (v: ConfigSaveResponse) => void;
    mockedApi.saveConfig.mockReturnValue(new Promise(r => { resolve = r; }));
    renderWithStore(<ConfigPanel />);
    await act(async () => {
      fireEvent.click(screen.getByTestId('save-btn'));
    });
    expect(screen.getByTestId('save-loading')).toBeInTheDocument();
    await act(async () => { resolve!(defaultSaveResponse); });
  });

  it('shows extreme goal warning when accuracy >= 0.99', () => {
    renderWithStore(<ConfigPanel />);
    fireEvent.change(screen.getByTestId('accuracy-input'), { target: { value: '0.99' } });
    expect(screen.getByTestId('extreme-goal-warning')).toBeInTheDocument();
  });

  it('shows extreme goal warning when fp_rate <= 0.001', () => {
    renderWithStore(<ConfigPanel />);
    fireEvent.change(screen.getByTestId('fp-rate-input'), { target: { value: '0.001' } });
    expect(screen.getByTestId('extreme-goal-warning')).toBeInTheDocument();
  });

  it('shows extreme goal warning when fn_rate <= 0.001', () => {
    renderWithStore(<ConfigPanel />);
    fireEvent.change(screen.getByTestId('fn-rate-input'), { target: { value: '0.0001' } });
    expect(screen.getByTestId('extreme-goal-warning')).toBeInTheDocument();
  });

  it('shows extreme goal warning when coord_error <= 0.5 in align mode', () => {
    renderWithStore(<ConfigPanel />);
    fireEvent.click(screen.getByTestId('mode-align'));
    fireEvent.change(screen.getByTestId('coord-error-input'), { target: { value: '0.5' } });
    expect(screen.getByTestId('extreme-goal-warning')).toBeInTheDocument();
  });

  it('does not show extreme warning when values are null', () => {
    renderWithStore(<ConfigPanel />);
    expect(screen.queryByTestId('extreme-goal-warning')).not.toBeInTheDocument();
  });

  it('does not show extreme warning when accuracy is within normal range', () => {
    renderWithStore(<ConfigPanel />);
    fireEvent.change(screen.getByTestId('accuracy-input'), { target: { value: '0.95' } });
    expect(screen.queryByTestId('extreme-goal-warning')).not.toBeInTheDocument();
  });

  it('loads config mode from Redux store', () => {
    const store = makeStore({ mode: 'align' });
    renderWithStore(<ConfigPanel />, store);
    const radio = screen.getByTestId('mode-align') as HTMLInputElement;
    expect(radio.checked).toBe(true);
  });

  it('loads max_iteration from Redux store', () => {
    const store = makeStore({ max_iteration: 7 });
    renderWithStore(<ConfigPanel />, store);
    const input = screen.getByTestId('max-iteration-input') as HTMLInputElement;
    expect(input.value).toBe('7');
  });

  it('loads success_criteria from Redux store', () => {
    const store = makeStore({
      success_criteria: { accuracy: 0.9, fp_rate: null, fn_rate: null, coord_error: null },
    });
    renderWithStore(<ConfigPanel />, store);
    const input = screen.getByTestId('accuracy-input') as HTMLInputElement;
    expect(input.value).toBe('0.9');
  });

  it('save button is disabled while saving', async () => {
    let resolve: (v: ConfigSaveResponse) => void;
    mockedApi.saveConfig.mockReturnValue(new Promise(r => { resolve = r; }));
    renderWithStore(<ConfigPanel />);
    await act(async () => {
      fireEvent.click(screen.getByTestId('save-btn'));
    });
    const btn = screen.getByTestId('save-btn') as HTMLButtonElement;
    expect(btn.disabled).toBe(true);
    await act(async () => { resolve!(defaultSaveResponse); });
  });

  it('save button passes config with current mode to saveConfig', async () => {
    renderWithStore(<ConfigPanel />);
    fireEvent.click(screen.getByTestId('mode-align'));
    await act(async () => {
      fireEvent.click(screen.getByTestId('save-btn'));
    });
    await waitFor(() => {
      expect(mockedApi.saveConfig).toHaveBeenCalledWith(
        expect.objectContaining({ mode: 'align' })
      );
    });
  });
});
