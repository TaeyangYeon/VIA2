import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore, combineReducers } from '@reduxjs/toolkit';
import resultReducer from '../store/slices/resultSlice';
import ResultPanel from '../components/panels/ResultPanel';
import type { ExecutionResult } from '../services/types';

const rootReducer = combineReducers({ result: resultReducer });

const defaultResult: ExecutionResult = {
  summary: null,
  pipeline: null,
  inspection_plan: null,
  blueprint_svg: null,
  parameter_sheet: null,
  metrics: null,
  item_results: null,
  lighting_suggestions: null,
  improvement_suggestions: null,
  decision: null,
  decision_reason: null,
};

const makeStore = (preloaded?: Partial<ExecutionResult>) =>
  configureStore({
    reducer: rootReducer,
    preloadedState: preloaded ? { result: { ...defaultResult, ...preloaded } } : undefined,
  });

const renderWithStore = (ui: React.ReactElement, store = makeStore()) =>
  ({ ...render(<Provider store={store}>{ui}</Provider>), store });

describe('ResultPanel', () => {
  beforeEach(() => {
    Object.defineProperty(global.URL, 'createObjectURL', {
      writable: true,
      value: jest.fn(() => 'blob:mock'),
    });
    Object.defineProperty(global.URL, 'revokeObjectURL', {
      writable: true,
      value: jest.fn(),
    });
    jest.spyOn(window, 'alert').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders without crashing', () => {
    const { container } = renderWithStore(<ResultPanel />);
    expect(container).toBeTruthy();
  });

  it('has data-testid="result-panel"', () => {
    renderWithStore(<ResultPanel />);
    expect(screen.getByTestId('result-panel')).toBeInTheDocument();
  });

  it('shows empty state when no result data', () => {
    renderWithStore(<ResultPanel />);
    expect(screen.getByTestId('result-empty-state')).toBeInTheDocument();
  });

  it('does not show empty state when summary is set', () => {
    const store = makeStore({ summary: 'Pipeline completed' });
    renderWithStore(<ResultPanel />, store);
    expect(screen.queryByTestId('result-empty-state')).not.toBeInTheDocument();
  });

  it('does not show empty state when decision is set', () => {
    const store = makeStore({ decision: 'rule_based_ok' });
    renderWithStore(<ResultPanel />, store);
    expect(screen.queryByTestId('result-empty-state')).not.toBeInTheDocument();
  });

  it('shows result-summary text when summary is available', () => {
    const store = makeStore({ summary: 'Pipeline completed successfully' });
    renderWithStore(<ResultPanel />, store);
    expect(screen.getByTestId('result-summary').textContent).toContain('Pipeline completed successfully');
  });

  it('shows decision-card when decision is set', () => {
    const store = makeStore({ decision: 'rule_based_ok' });
    renderWithStore(<ResultPanel />, store);
    expect(screen.getByTestId('decision-card')).toBeInTheDocument();
  });

  it('shows decision-reason when available', () => {
    const store = makeStore({ decision: 'rule_based_ok', decision_reason: 'All checks passed' });
    renderWithStore(<ResultPanel />, store);
    expect(screen.getByTestId('decision-reason').textContent).toContain('All checks passed');
  });

  it('does not show decision-card when decision is null', () => {
    const store = makeStore({ summary: 'Done' });
    renderWithStore(<ResultPanel />, store);
    expect(screen.queryByTestId('decision-card')).not.toBeInTheDocument();
  });

  it('shows export-pdf-btn when result is available', () => {
    const store = makeStore({ summary: 'Done' });
    renderWithStore(<ResultPanel />, store);
    expect(screen.getByTestId('export-pdf-btn')).toBeInTheDocument();
  });

  it('shows export-svg-btn when blueprint_svg is set', () => {
    const store = makeStore({ blueprint_svg: '<svg></svg>', summary: 'Done' });
    renderWithStore(<ResultPanel />, store);
    expect(screen.getByTestId('export-svg-btn')).toBeInTheDocument();
  });

  it('does not show export-svg-btn when blueprint_svg is null', () => {
    const store = makeStore({ summary: 'Done' });
    renderWithStore(<ResultPanel />, store);
    expect(screen.queryByTestId('export-svg-btn')).not.toBeInTheDocument();
  });

  it('calls URL.createObjectURL when export-svg-btn is clicked', () => {
    const store = makeStore({ blueprint_svg: '<svg></svg>', summary: 'Done' });
    renderWithStore(<ResultPanel />, store);
    fireEvent.click(screen.getByTestId('export-svg-btn'));
    expect(global.URL.createObjectURL).toHaveBeenCalled();
  });

  it('calls window.alert when export-pdf-btn is clicked', () => {
    const store = makeStore({ summary: 'Done' });
    renderWithStore(<ResultPanel />, store);
    fireEvent.click(screen.getByTestId('export-pdf-btn'));
    expect(window.alert).toHaveBeenCalledWith('PDF export coming soon');
  });

  it('shows improvement suggestions when available', () => {
    const store = makeStore({
      summary: 'Done',
      improvement_suggestions: ['Add more lighting', 'Use a different filter'],
    });
    renderWithStore(<ResultPanel />, store);
    expect(screen.getByText('Add more lighting')).toBeInTheDocument();
    expect(screen.getByText('Use a different filter')).toBeInTheDocument();
  });

  it('shows blueprint-viewer when blueprint_svg is set', () => {
    const store = makeStore({ blueprint_svg: '<svg></svg>', summary: 'Done' });
    renderWithStore(<ResultPanel />, store);
    expect(screen.getByTestId('blueprint-viewer')).toBeInTheDocument();
  });

  it('shows metrics-table when item_results is available', () => {
    const store = makeStore({
      summary: 'Done',
      item_results: [
        { item_id: 'i1', category: 'defect', passed: true, accuracy: 0.9, fp_rate: 0.05, fn_rate: 0.05 },
      ],
    });
    renderWithStore(<ResultPanel />, store);
    expect(screen.getByTestId('metrics-table')).toBeInTheDocument();
  });

  it('shows lighting-suggestion-list when lighting_suggestions is available', () => {
    const store = makeStore({
      summary: 'Done',
      lighting_suggestions: ['Use ring light'],
    });
    renderWithStore(<ResultPanel />, store);
    expect(screen.getByTestId('lighting-suggestion-list')).toBeInTheDocument();
  });
});
