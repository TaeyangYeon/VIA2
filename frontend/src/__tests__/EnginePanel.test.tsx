import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import engineReducer from '../store/slices/engineSlice';
import EnginePanel from '../components/panels/EnginePanel';
import * as api from '../services/api';
import type { EngineSettings } from '../services/types';

jest.mock('../services/api');
const mockedApi = api as jest.Mocked<typeof api>;

const defaultEngine: EngineSettings = {
  mode: 'local',
  local_ollama_url: 'http://127.0.0.1:11434',
  remote_url: null,
  remote_type: 'colab',
  remote_auth_token: null,
  model_name: 'qwen2.5-coder:7b',
};

const makeStore = (preloadedEngine?: Partial<EngineSettings>) =>
  configureStore({
    reducer: { engine: engineReducer },
    preloadedState: preloadedEngine
      ? { engine: { ...defaultEngine, ...preloadedEngine } }
      : undefined,
  });

const renderWithStore = (ui: React.ReactElement, store = makeStore()) =>
  ({ ...render(<Provider store={store}>{ui}</Provider>), store });

describe('EnginePanel component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedApi.getEngine.mockResolvedValue(defaultEngine);
    mockedApi.updateEngine.mockResolvedValue(defaultEngine);
  });

  it('renders without crashing', () => {
    const { container } = renderWithStore(<EnginePanel />);
    expect(container).toBeTruthy();
  });

  it('has data-testid="engine-panel"', () => {
    renderWithStore(<EnginePanel />);
    expect(screen.getByTestId('engine-panel')).toBeInTheDocument();
  });

  it('shows local mode as default', () => {
    renderWithStore(<EnginePanel />);
    const localRadio = screen.getByTestId('mode-local');
    expect(localRadio).toBeInTheDocument();
  });

  it('shows local_ollama_url input in local mode', () => {
    renderWithStore(<EnginePanel />);
    expect(screen.getByTestId('local-ollama-url-input')).toBeInTheDocument();
  });

  it('shows model_name input in local mode', () => {
    renderWithStore(<EnginePanel />);
    expect(screen.getByTestId('model-name-input')).toBeInTheDocument();
  });

  it('hides remote fields in local mode', () => {
    renderWithStore(<EnginePanel />);
    expect(screen.queryByTestId('remote-url-input')).not.toBeInTheDocument();
    expect(screen.queryByTestId('remote-auth-token-input')).not.toBeInTheDocument();
  });

  it('switches to remote mode when remote radio clicked', () => {
    renderWithStore(<EnginePanel />);
    fireEvent.click(screen.getByTestId('mode-remote'));
    expect(screen.getByTestId('remote-type-select')).toBeInTheDocument();
  });

  it('shows remote fields in remote mode', () => {
    renderWithStore(<EnginePanel />);
    fireEvent.click(screen.getByTestId('mode-remote'));
    expect(screen.getByTestId('remote-url-input')).toBeInTheDocument();
    expect(screen.getByTestId('remote-auth-token-input')).toBeInTheDocument();
  });

  it('remote_auth_token input is password type', () => {
    renderWithStore(<EnginePanel />);
    fireEvent.click(screen.getByTestId('mode-remote'));
    const input = screen.getByTestId('remote-auth-token-input') as HTMLInputElement;
    expect(input.type).toBe('password');
  });

  it('has save button', () => {
    renderWithStore(<EnginePanel />);
    expect(screen.getByTestId('save-btn')).toBeInTheDocument();
  });

  it('has test-connection button', () => {
    renderWithStore(<EnginePanel />);
    expect(screen.getByTestId('test-connection-btn')).toBeInTheDocument();
  });

  it('calls updateEngine on save', async () => {
    renderWithStore(<EnginePanel />);
    await act(async () => {
      fireEvent.click(screen.getByTestId('save-btn'));
    });
    await waitFor(() => {
      expect(mockedApi.updateEngine).toHaveBeenCalled();
    });
  });

  it('dispatches setEngine after successful save', async () => {
    const store = makeStore();
    renderWithStore(<EnginePanel />, store);
    await act(async () => {
      fireEvent.click(screen.getByTestId('save-btn'));
    });
    await waitFor(() => {
      expect(mockedApi.updateEngine).toHaveBeenCalled();
    });
    expect(store.getState().engine).toEqual(defaultEngine);
  });

  it('shows success feedback after save', async () => {
    renderWithStore(<EnginePanel />);
    await act(async () => {
      fireEvent.click(screen.getByTestId('save-btn'));
    });
    await waitFor(() => {
      expect(screen.getByTestId('save-success')).toBeInTheDocument();
    });
  });

  it('shows error feedback when save fails', async () => {
    mockedApi.updateEngine.mockRejectedValue(new Error('Network error'));
    renderWithStore(<EnginePanel />);
    await act(async () => {
      fireEvent.click(screen.getByTestId('save-btn'));
    });
    await waitFor(() => {
      expect(screen.getByTestId('save-error')).toBeInTheDocument();
    });
  });

  it('calls getEngine on test connection', async () => {
    renderWithStore(<EnginePanel />);
    await act(async () => {
      fireEvent.click(screen.getByTestId('test-connection-btn'));
    });
    await waitFor(() => {
      expect(mockedApi.getEngine).toHaveBeenCalled();
    });
  });

  it('shows connection success after test connection', async () => {
    renderWithStore(<EnginePanel />);
    await act(async () => {
      fireEvent.click(screen.getByTestId('test-connection-btn'));
    });
    await waitFor(() => {
      expect(screen.getByTestId('connection-success')).toBeInTheDocument();
    });
  });

  it('shows connection error when test connection fails', async () => {
    mockedApi.getEngine.mockRejectedValue(new Error('Connection refused'));
    renderWithStore(<EnginePanel />);
    await act(async () => {
      fireEvent.click(screen.getByTestId('test-connection-btn'));
    });
    await waitFor(() => {
      expect(screen.getByTestId('connection-error')).toBeInTheDocument();
    });
  });

  it('local_ollama_url input reflects Redux state', () => {
    const store = makeStore({ local_ollama_url: 'http://custom:11434' });
    renderWithStore(<EnginePanel />, store);
    const input = screen.getByTestId('local-ollama-url-input') as HTMLInputElement;
    expect(input.value).toBe('http://custom:11434');
  });

  it('model_name input reflects Redux state', () => {
    const store = makeStore({ model_name: 'llama3:8b' });
    renderWithStore(<EnginePanel />, store);
    const input = screen.getByTestId('model-name-input') as HTMLInputElement;
    expect(input.value).toBe('llama3:8b');
  });

  it('remote_type select has colab/azure/custom options', () => {
    renderWithStore(<EnginePanel />);
    fireEvent.click(screen.getByTestId('mode-remote'));
    const select = screen.getByTestId('remote-type-select') as HTMLSelectElement;
    const options = Array.from(select.options).map(o => o.value);
    expect(options).toContain('colab');
    expect(options).toContain('azure');
    expect(options).toContain('custom');
  });

  it('shows saving indicator while save is in progress', async () => {
    let resolve: (v: EngineSettings) => void;
    mockedApi.updateEngine.mockReturnValue(new Promise(r => { resolve = r; }));
    renderWithStore(<EnginePanel />);
    await act(async () => {
      fireEvent.click(screen.getByTestId('save-btn'));
    });
    expect(screen.getByTestId('save-loading')).toBeInTheDocument();
    await act(async () => { resolve!(defaultEngine); });
  });
});
