import { store } from '../store';

describe('Redux store — slice presence', () => {
  it('has all required top-level slices', () => {
    const state = store.getState();
    expect(state).toHaveProperty('project');
    expect(state).toHaveProperty('engine');
    expect(state).toHaveProperty('images');
    expect(state).toHaveProperty('roi');
    expect(state).toHaveProperty('config');
    expect(state).toHaveProperty('directives');
    expect(state).toHaveProperty('execution');
    expect(state).toHaveProperty('result');
    expect(state).toHaveProperty('light_test');
    expect(state).toHaveProperty('logs');
  });
});

describe('Redux store — initial states', () => {
  let state: ReturnType<typeof store.getState>;

  beforeEach(() => {
    state = store.getState();
  });

  it('project initial state', () => {
    expect(state.project).toEqual({ name: '', created_at: '' });
  });

  it('engine initial state', () => {
    expect(state.engine).toEqual({
      mode: 'local',
      local_ollama_url: 'http://127.0.0.1:11434',
      remote_url: null,
      remote_type: 'colab',
      remote_auth_token: null,
      model_name: 'qwen2.5-coder:7b',
    });
  });

  it('images initial state', () => {
    expect(state.images).toEqual({ analysis: [], test: [] });
  });

  it('roi initial state is null', () => {
    expect(state.roi).toBeNull();
  });

  it('config initial state', () => {
    expect(state.config).toEqual({
      mode: 'inspection',
      max_iteration: 3,
      success_criteria: {
        accuracy: null,
        fp_rate: null,
        fn_rate: null,
        coord_error: null,
      },
    });
  });

  it('directives initial state', () => {
    expect(state.directives).toEqual({
      orchestrator: '',
      spec: '',
      image_analysis: '',
      depth: '',
      material: '',
      pipeline_composer: '',
      vision_judge: '',
      inspection_plan: '',
      test: '',
    });
  });

  it('execution initial state', () => {
    expect(state.execution).toEqual({
      status: 'idle',
      execution_id: null,
      current_agent: null,
      current_iteration: 0,
      goal_validation: null,
      progress: 0,
    });
  });

  it('result initial state', () => {
    expect(state.result).toEqual({
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
    });
  });

  it('light_test initial state', () => {
    expect(state.light_test).toEqual({
      image: null,
      lights: [],
      camera_view: 'front',
      rendered_result: null,
    });
  });

  it('logs initial state is empty array', () => {
    expect(state.logs).toEqual([]);
  });
});
