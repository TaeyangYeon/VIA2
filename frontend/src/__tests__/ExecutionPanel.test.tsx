import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore, combineReducers } from '@reduxjs/toolkit';
import executionReducer from '../store/slices/executionSlice';
import resultReducer from '../store/slices/resultSlice';
import imagesReducer from '../store/slices/imagesSlice';
import configReducer from '../store/slices/configSlice';
import directivesReducer from '../store/slices/directivesSlice';
import ExecutionPanel from '../components/panels/ExecutionPanel';
import * as api from '../services/api';
import type { ImageMetadata, ExecutionStatus } from '../services/types';

jest.mock('../services/api');
const mockedApi = api as jest.Mocked<typeof api>;

const mockImage: ImageMetadata = {
  id: 'img1',
  original_filename: 'test.jpg',
  label: 'test',
  index: 0,
  file_size: 1024,
  upload_timestamp: '2024-01-01T00:00:00Z',
  file_path: '/tmp/test.jpg',
  group: 'analysis',
};

const runningExecution = {
  status: 'running' as const,
  execution_id: 'exec-1',
  current_agent: 'spec',
  current_iteration: 1,
  goal_validation: null,
  progress: 50,
};

const rootReducer = combineReducers({
  execution: executionReducer,
  result: resultReducer,
  images: imagesReducer,
  config: configReducer,
  directives: directivesReducer,
});

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const makeStore = (preloaded?: any) =>
  configureStore({ reducer: rootReducer, preloadedState: preloaded });

const renderWithStore = (ui: React.ReactElement, store = makeStore()) =>
  ({ ...render(<Provider store={store}>{ui}</Provider>), store });

describe('ExecutionPanel', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    mockedApi.startExecution.mockResolvedValue({ execution_id: 'exec-1', status: 'pending' });
    mockedApi.cancelExecution.mockResolvedValue({ message: 'cancelled', execution_id: 'exec-1' });
    mockedApi.getExecution.mockResolvedValue({
      execution_id: 'exec-1',
      status: 'running',
      current_agent: 'spec',
      current_iteration: 1,
      goal_validation: null,
      progress: 50,
    } as ExecutionStatus);
  });

  afterEach(() => {
    act(() => { jest.runOnlyPendingTimers(); });
    jest.useRealTimers();
  });

  it('renders without crashing', () => {
    const { container } = renderWithStore(<ExecutionPanel />);
    expect(container).toBeTruthy();
  });

  it('has data-testid="execution-panel"', () => {
    renderWithStore(<ExecutionPanel />);
    expect(screen.getByTestId('execution-panel')).toBeInTheDocument();
  });

  it('shows start button in idle state', () => {
    renderWithStore(<ExecutionPanel />);
    expect(screen.getByTestId('start-btn')).toBeInTheDocument();
  });

  it('disables start button when no images uploaded', () => {
    renderWithStore(<ExecutionPanel />);
    const btn = screen.getByTestId('start-btn') as HTMLButtonElement;
    expect(btn.disabled).toBe(true);
  });

  it('enables start button when images are present', () => {
    const store = makeStore({ images: { analysis: [mockImage], test: [] } });
    renderWithStore(<ExecutionPanel />, store);
    const btn = screen.getByTestId('start-btn') as HTMLButtonElement;
    expect(btn.disabled).toBe(false);
  });

  it('calls startExecution when start is clicked with images present', async () => {
    const store = makeStore({ images: { analysis: [mockImage], test: [] } });
    renderWithStore(<ExecutionPanel />, store);
    await act(async () => {
      fireEvent.click(screen.getByTestId('start-btn'));
    });
    await waitFor(() => {
      expect(mockedApi.startExecution).toHaveBeenCalled();
    });
  });

  it('shows stop button when status is running', () => {
    const store = makeStore({ execution: runningExecution });
    renderWithStore(<ExecutionPanel />, store);
    expect(screen.getByTestId('stop-btn')).toBeInTheDocument();
  });

  it('does not show stop button in idle state', () => {
    renderWithStore(<ExecutionPanel />);
    expect(screen.queryByTestId('stop-btn')).not.toBeInTheDocument();
  });

  it('does not show start button when running', () => {
    const store = makeStore({ execution: runningExecution });
    renderWithStore(<ExecutionPanel />, store);
    expect(screen.queryByTestId('start-btn')).not.toBeInTheDocument();
  });

  it('calls cancelExecution with execution_id when stop is clicked', async () => {
    const store = makeStore({ execution: runningExecution });
    renderWithStore(<ExecutionPanel />, store);
    await act(async () => {
      fireEvent.click(screen.getByTestId('stop-btn'));
    });
    await waitFor(() => {
      expect(mockedApi.cancelExecution).toHaveBeenCalledWith('exec-1');
    });
  });

  it('shows current agent display when running', () => {
    const store = makeStore({ execution: runningExecution });
    renderWithStore(<ExecutionPanel />, store);
    expect(screen.getByTestId('current-agent-display')).toBeInTheDocument();
  });

  it('shows current agent name', () => {
    const store = makeStore({ execution: runningExecution });
    renderWithStore(<ExecutionPanel />, store);
    expect(screen.getByTestId('current-agent-display').textContent).toContain('spec');
  });

  it('shows iteration counter when running', () => {
    const store = makeStore({ execution: runningExecution });
    renderWithStore(<ExecutionPanel />, store);
    expect(screen.getByTestId('iteration-counter')).toBeInTheDocument();
  });

  it('shows progress bar when running', () => {
    const store = makeStore({ execution: runningExecution });
    renderWithStore(<ExecutionPanel />, store);
    expect(screen.getByTestId('progress-bar')).toBeInTheDocument();
  });

  it('shows completed status message', () => {
    const store = makeStore({
      execution: {
        status: 'completed',
        execution_id: 'exec-1',
        current_agent: null,
        current_iteration: 3,
        goal_validation: null,
        progress: 100,
      },
    });
    renderWithStore(<ExecutionPanel />, store);
    expect(screen.getByTestId('status-completed')).toBeInTheDocument();
  });

  it('shows start button again after completion', () => {
    const store = makeStore({
      execution: {
        status: 'completed',
        execution_id: 'exec-1',
        current_agent: null,
        current_iteration: 3,
        goal_validation: null,
        progress: 100,
      },
    });
    renderWithStore(<ExecutionPanel />, store);
    expect(screen.getByTestId('start-btn')).toBeInTheDocument();
  });

  it('shows failed status message', () => {
    const store = makeStore({
      execution: {
        status: 'failed',
        execution_id: 'exec-1',
        current_agent: null,
        current_iteration: 1,
        goal_validation: null,
        progress: 0,
      },
    });
    renderWithStore(<ExecutionPanel />, store);
    expect(screen.getByTestId('status-failed')).toBeInTheDocument();
  });

  it('shows start (retry) button after failure', () => {
    const store = makeStore({
      execution: {
        status: 'failed',
        execution_id: 'exec-1',
        current_agent: null,
        current_iteration: 1,
        goal_validation: null,
        progress: 0,
      },
    });
    renderWithStore(<ExecutionPanel />, store);
    expect(screen.getByTestId('start-btn')).toBeInTheDocument();
  });

  it('shows cancelled status message', () => {
    const store = makeStore({
      execution: {
        status: 'cancelled',
        execution_id: 'exec-1',
        current_agent: null,
        current_iteration: 1,
        goal_validation: null,
        progress: 0,
      },
    });
    renderWithStore(<ExecutionPanel />, store);
    expect(screen.getByTestId('status-cancelled')).toBeInTheDocument();
  });

  it('shows goal_validation warnings when present', () => {
    const store = makeStore({
      execution: {
        ...runningExecution,
        goal_validation: { valid: false, warnings: ['Warning: extreme threshold'] },
      },
    });
    renderWithStore(<ExecutionPanel />, store);
    expect(screen.getByTestId('goal-validation-warnings')).toBeInTheDocument();
  });

  it('shows warning text content', () => {
    const store = makeStore({
      execution: {
        ...runningExecution,
        goal_validation: { valid: false, warnings: ['Extreme threshold detected'] },
      },
    });
    renderWithStore(<ExecutionPanel />, store);
    expect(screen.getByTestId('goal-validation-warnings').textContent).toContain(
      'Extreme threshold detected'
    );
  });

  it('does not show goal_validation warnings when null', () => {
    const store = makeStore({ execution: runningExecution });
    renderWithStore(<ExecutionPanel />, store);
    expect(screen.queryByTestId('goal-validation-warnings')).not.toBeInTheDocument();
  });

  it('polls getExecution when execution_id is set and status is running', async () => {
    const store = makeStore({
      execution: runningExecution,
      images: { analysis: [mockImage], test: [] },
    });
    renderWithStore(<ExecutionPanel />, store);

    await act(async () => {
      jest.advanceTimersByTime(2000);
    });

    expect(mockedApi.getExecution).toHaveBeenCalledWith('exec-1');
  });

  it('updates execution state from poll response', async () => {
    mockedApi.getExecution.mockResolvedValue({
      execution_id: 'exec-1',
      status: 'running',
      current_agent: 'pipeline_composer',
      current_iteration: 2,
      goal_validation: null,
      progress: 70,
    } as ExecutionStatus);

    const store = makeStore({
      execution: runningExecution,
      images: { analysis: [mockImage], test: [] },
    });
    renderWithStore(<ExecutionPanel />, store);

    await act(async () => {
      jest.advanceTimersByTime(2000);
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(store.getState().execution.current_iteration).toBe(2);
    });
  });

  it('dispatches setResult when poll returns a result', async () => {
    const mockResult = {
      summary: 'Done',
      pipeline: null,
      inspection_plan: null,
      blueprint_svg: null,
      parameter_sheet: null,
      metrics: null,
      item_results: null,
      lighting_suggestions: null,
      improvement_suggestions: null,
      decision: 'pass',
      decision_reason: 'all checks passed',
    };
    mockedApi.getExecution.mockResolvedValue({
      execution_id: 'exec-1',
      status: 'completed',
      current_agent: null,
      current_iteration: 3,
      goal_validation: null,
      progress: 100,
      result: mockResult,
    } as ExecutionStatus);

    const store = makeStore({
      execution: runningExecution,
      images: { analysis: [mockImage], test: [] },
    });
    renderWithStore(<ExecutionPanel />, store);

    await act(async () => {
      jest.advanceTimersByTime(2000);
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(store.getState().result.summary).toBe('Done');
    });
  });
});
