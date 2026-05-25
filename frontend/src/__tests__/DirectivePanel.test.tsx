import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import directivesReducer from '../store/slices/directivesSlice';
import DirectivePanel from '../components/panels/DirectivePanel';
import * as api from '../services/api';
import type { AgentDirectives } from '../services/types';

jest.mock('../services/api');
const mockedApi = api as jest.Mocked<typeof api>;

const defaultDirectives: AgentDirectives = {
  orchestrator: '',
  spec: '',
  image_analysis: '',
  depth: '',
  material: '',
  pipeline_composer: '',
  vision_judge: '',
  inspection_plan: '',
  test: '',
};

const makeStore = (preloaded?: Partial<AgentDirectives>) =>
  configureStore({
    reducer: { directives: directivesReducer },
    preloadedState: preloaded
      ? { directives: { ...defaultDirectives, ...preloaded } }
      : undefined,
  });

const renderWithStore = (ui: React.ReactElement, store = makeStore()) =>
  ({ ...render(<Provider store={store}>{ui}</Provider>), store });

const AGENT_KEYS: Array<keyof AgentDirectives> = [
  'orchestrator', 'spec', 'image_analysis', 'depth', 'material',
  'pipeline_composer', 'vision_judge', 'inspection_plan', 'test',
];

describe('DirectivePanel component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedApi.getDirectives.mockResolvedValue(defaultDirectives);
    mockedApi.saveDirectives.mockResolvedValue(defaultDirectives);
  });

  it('renders without crashing', () => {
    const { container } = renderWithStore(<DirectivePanel />);
    expect(container).toBeTruthy();
  });

  it('has data-testid="directive-panel"', () => {
    renderWithStore(<DirectivePanel />);
    expect(screen.getByTestId('directive-panel')).toBeInTheDocument();
  });

  it('renders all 9 agent card headers', () => {
    renderWithStore(<DirectivePanel />);
    AGENT_KEYS.forEach(key => {
      expect(screen.getByTestId(`agent-card-${key}`)).toBeInTheDocument();
    });
  });

  it('renders card header for each agent', () => {
    renderWithStore(<DirectivePanel />);
    AGENT_KEYS.forEach(key => {
      expect(screen.getByTestId(`agent-header-${key}`)).toBeInTheDocument();
    });
  });

  it('cards are collapsed by default (textarea not visible)', () => {
    renderWithStore(<DirectivePanel />);
    AGENT_KEYS.forEach(key => {
      const textarea = screen.getByTestId(`directive-textarea-${key}`);
      expect(textarea).not.toBeVisible();
    });
  });

  it('clicking a card header expands it', () => {
    renderWithStore(<DirectivePanel />);
    fireEvent.click(screen.getByTestId('agent-header-orchestrator'));
    expect(screen.getByTestId('directive-textarea-orchestrator')).toBeVisible();
  });

  it('clicking an expanded card header collapses it', () => {
    renderWithStore(<DirectivePanel />);
    fireEvent.click(screen.getByTestId('agent-header-orchestrator'));
    fireEvent.click(screen.getByTestId('agent-header-orchestrator'));
    expect(screen.getByTestId('directive-textarea-orchestrator')).not.toBeVisible();
  });

  it('has save-all button', () => {
    renderWithStore(<DirectivePanel />);
    expect(screen.getByTestId('save-all-btn')).toBeInTheDocument();
  });

  it('has clear-all button', () => {
    renderWithStore(<DirectivePanel />);
    expect(screen.getByTestId('clear-all-btn')).toBeInTheDocument();
  });

  it('calls saveDirectives on save all', async () => {
    renderWithStore(<DirectivePanel />);
    await act(async () => {
      fireEvent.click(screen.getByTestId('save-all-btn'));
    });
    await waitFor(() => {
      expect(mockedApi.saveDirectives).toHaveBeenCalled();
    });
  });

  it('dispatches setDirectives after successful save', async () => {
    const filled: AgentDirectives = {
      ...defaultDirectives,
      orchestrator: 'Test directive',
    };
    mockedApi.saveDirectives.mockResolvedValue(filled);
    const store = makeStore({ orchestrator: 'Test directive' });
    renderWithStore(<DirectivePanel />, store);
    await act(async () => {
      fireEvent.click(screen.getByTestId('save-all-btn'));
    });
    await waitFor(() => {
      expect(mockedApi.saveDirectives).toHaveBeenCalled();
    });
    expect(store.getState().directives.orchestrator).toBe('Test directive');
  });

  it('clear all resets all textarea values to empty', async () => {
    const store = makeStore({ orchestrator: 'some value', spec: 'other value' });
    renderWithStore(<DirectivePanel />, store);
    await act(async () => {
      fireEvent.click(screen.getByTestId('clear-all-btn'));
    });
    AGENT_KEYS.forEach(key => {
      const textarea = screen.getByTestId(`directive-textarea-${key}`) as HTMLTextAreaElement;
      expect(textarea.value).toBe('');
    });
  });

  it('shows save success after successful save', async () => {
    renderWithStore(<DirectivePanel />);
    await act(async () => {
      fireEvent.click(screen.getByTestId('save-all-btn'));
    });
    await waitFor(() => {
      expect(screen.getByTestId('save-success')).toBeInTheDocument();
    });
  });

  it('shows save error when save fails', async () => {
    mockedApi.saveDirectives.mockRejectedValue(new Error('Save failed'));
    renderWithStore(<DirectivePanel />);
    await act(async () => {
      fireEvent.click(screen.getByTestId('save-all-btn'));
    });
    await waitFor(() => {
      expect(screen.getByTestId('save-error')).toBeInTheDocument();
    });
  });

  it('textarea reflects Redux state value', () => {
    const store = makeStore({ orchestrator: 'custom directive text' });
    renderWithStore(<DirectivePanel />, store);
    fireEvent.click(screen.getByTestId('agent-header-orchestrator'));
    const textarea = screen.getByTestId('directive-textarea-orchestrator') as HTMLTextAreaElement;
    expect(textarea.value).toBe('custom directive text');
  });

  it('typing in textarea updates local state', () => {
    renderWithStore(<DirectivePanel />);
    fireEvent.click(screen.getByTestId('agent-header-orchestrator'));
    const textarea = screen.getByTestId('directive-textarea-orchestrator') as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: 'new directive' } });
    expect(textarea.value).toBe('new directive');
  });

  it('shows save loading indicator while saving', async () => {
    let resolve: (v: AgentDirectives) => void;
    mockedApi.saveDirectives.mockReturnValue(new Promise(r => { resolve = r; }));
    renderWithStore(<DirectivePanel />);
    await act(async () => {
      fireEvent.click(screen.getByTestId('save-all-btn'));
    });
    expect(screen.getByTestId('save-loading')).toBeInTheDocument();
    await act(async () => { resolve!(defaultDirectives); });
  });

  it('saveDirectives is called with correct directives payload', async () => {
    const store = makeStore({ orchestrator: 'pipeline logic', spec: 'spec text' });
    renderWithStore(<DirectivePanel />, store);
    await act(async () => {
      fireEvent.click(screen.getByTestId('save-all-btn'));
    });
    await waitFor(() => {
      expect(mockedApi.saveDirectives).toHaveBeenCalledWith(
        expect.objectContaining({ orchestrator: 'pipeline logic', spec: 'spec text' })
      );
    });
  });
});
