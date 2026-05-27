import projectReducer, { setProject } from '../store/slices/projectSlice';
import engineReducer, { setEngine } from '../store/slices/engineSlice';
import imagesReducer, {
  addImage,
  setAnalysisImages,
  setTestImages,
  removeImage,
  clearImages,
} from '../store/slices/imagesSlice';
import roiReducer, { setRoi, clearRoi } from '../store/slices/roiSlice';
import configReducer, { setConfig } from '../store/slices/configSlice';
import directivesReducer, {
  setDirectives,
  updateDirective,
} from '../store/slices/directivesSlice';
import executionReducer, {
  setExecutionStatus,
  setExecutionId,
  setCurrentAgent,
  setCurrentIteration,
  setGoalValidation,
  setProgress,
  setExecution,
  resetExecution,
} from '../store/slices/executionSlice';
import resultReducer, { setResult, clearResult } from '../store/slices/resultSlice';
import lightTestReducer, {
  setLightTestImage,
  addLight,
  removeLight,
  updateLight,
  setCameraView,
  setRenderedResult,
  setAnalysisLoading,
  setAnalysisResult,
  setAnalysisError,
  clearAnalysis,
  clearLightTest,
} from '../store/slices/lightTestSlice';
import logsReducer, {
  addLog,
  setLogs,
  clearLogs,
} from '../store/slices/logsSlice';

import type { ImageMetadata, LightConfig, LogEntry } from '../services/types';

// ── projectSlice ──────────────────────────────────────────────────────────────
describe('projectSlice', () => {
  it('returns initial state', () => {
    expect(projectReducer(undefined, { type: '' })).toEqual({ name: '', created_at: '' });
  });

  it('setProject updates name and created_at', () => {
    const result = projectReducer(undefined, setProject({ name: 'My Project', created_at: '2024-01-01' }));
    expect(result).toEqual({ name: 'My Project', created_at: '2024-01-01' });
  });
});

// ── engineSlice ───────────────────────────────────────────────────────────────
describe('engineSlice', () => {
  const initial = {
    mode: 'local' as const,
    local_ollama_url: 'http://127.0.0.1:11434',
    remote_url: null,
    remote_type: 'colab',
    remote_auth_token: null,
    model_name: 'qwen2.5-coder:7b',
  };

  it('returns initial state', () => {
    expect(engineReducer(undefined, { type: '' })).toEqual(initial);
  });

  it('setEngine updates all fields', () => {
    const updated = { ...initial, mode: 'remote' as const, remote_url: 'http://example.com' };
    const result = engineReducer(undefined, setEngine(updated));
    expect(result.mode).toBe('remote');
    expect(result.remote_url).toBe('http://example.com');
  });
});

// ── imagesSlice ───────────────────────────────────────────────────────────────
describe('imagesSlice', () => {
  const analysisImage: ImageMetadata = {
    id: 'img-1',
    original_filename: 'ok_1.jpg',
    label: 'ok',
    index: 1,
    file_size: 12345,
    upload_timestamp: '2024-01-01T00:00:00Z',
    file_path: '/tmp/ok_1.jpg',
    group: 'analysis',
  };
  const testImage: ImageMetadata = { ...analysisImage, id: 'img-2', group: 'test' };

  it('returns initial state', () => {
    expect(imagesReducer(undefined, { type: '' })).toEqual({ analysis: [], test: [] });
  });

  it('addImage routes to analysis group', () => {
    const result = imagesReducer(undefined, addImage(analysisImage));
    expect(result.analysis).toHaveLength(1);
    expect(result.test).toHaveLength(0);
  });

  it('addImage routes to test group', () => {
    const result = imagesReducer(undefined, addImage(testImage));
    expect(result.test).toHaveLength(1);
    expect(result.analysis).toHaveLength(0);
  });

  it('setAnalysisImages replaces analysis array', () => {
    const result = imagesReducer(undefined, setAnalysisImages([analysisImage]));
    expect(result.analysis).toHaveLength(1);
  });

  it('setTestImages replaces test array', () => {
    const result = imagesReducer(undefined, setTestImages([testImage]));
    expect(result.test).toHaveLength(1);
  });

  it('removeImage removes from correct group', () => {
    const state = { analysis: [analysisImage], test: [testImage] };
    const result = imagesReducer(state, removeImage('img-1'));
    expect(result.analysis).toHaveLength(0);
    expect(result.test).toHaveLength(1);
  });

  it('clearImages empties both groups', () => {
    const state = { analysis: [analysisImage], test: [testImage] };
    const result = imagesReducer(state, clearImages());
    expect(result).toEqual({ analysis: [], test: [] });
  });
});

// ── roiSlice ──────────────────────────────────────────────────────────────────
describe('roiSlice', () => {
  it('returns null as initial state', () => {
    expect(roiReducer(undefined, { type: '' })).toBeNull();
  });

  it('setRoi stores coordinates', () => {
    const roi = { x1: 10, y1: 20, x2: 100, y2: 200 };
    expect(roiReducer(undefined, setRoi(roi))).toEqual(roi);
  });

  it('clearRoi resets to null', () => {
    const withRoi = roiReducer(undefined, setRoi({ x1: 0, y1: 0, x2: 50, y2: 50 }));
    expect(roiReducer(withRoi, clearRoi())).toBeNull();
  });
});

// ── configSlice ───────────────────────────────────────────────────────────────
describe('configSlice', () => {
  const initial = {
    mode: 'inspection' as const,
    max_iteration: 3,
    success_criteria: { accuracy: null, fp_rate: null, fn_rate: null, coord_error: null },
  };

  it('returns initial state', () => {
    expect(configReducer(undefined, { type: '' })).toEqual(initial);
  });

  it('setConfig updates state', () => {
    const result = configReducer(undefined, setConfig({ ...initial, max_iteration: 7 }));
    expect(result.max_iteration).toBe(7);
  });

  it('setConfig updates mode', () => {
    const result = configReducer(undefined, setConfig({ ...initial, mode: 'align' }));
    expect(result.mode).toBe('align');
  });
});

// ── directivesSlice ───────────────────────────────────────────────────────────
describe('directivesSlice', () => {
  const initial = {
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

  it('returns initial state', () => {
    expect(directivesReducer(undefined, { type: '' })).toEqual(initial);
  });

  it('setDirectives replaces all fields', () => {
    const result = directivesReducer(
      undefined,
      setDirectives({ ...initial, orchestrator: 'You are the orchestrator.' }),
    );
    expect(result.orchestrator).toBe('You are the orchestrator.');
  });

  it('updateDirective patches a single field', () => {
    const result = directivesReducer(
      undefined,
      updateDirective({ key: 'spec', value: 'Spec directive text' }),
    );
    expect(result.spec).toBe('Spec directive text');
    expect(result.orchestrator).toBe('');
  });
});

// ── executionSlice ────────────────────────────────────────────────────────────
describe('executionSlice', () => {
  const initial = {
    status: 'idle' as const,
    execution_id: null,
    current_agent: null,
    current_iteration: 0,
    goal_validation: null,
    progress: 0,
  };

  it('returns initial state', () => {
    expect(executionReducer(undefined, { type: '' })).toEqual(initial);
  });

  it('setExecutionStatus', () => {
    const result = executionReducer(undefined, setExecutionStatus('running'));
    expect(result.status).toBe('running');
  });

  it('setExecutionId', () => {
    const result = executionReducer(undefined, setExecutionId('exec-abc-123'));
    expect(result.execution_id).toBe('exec-abc-123');
  });

  it('setCurrentAgent', () => {
    const result = executionReducer(undefined, setCurrentAgent('orchestrator'));
    expect(result.current_agent).toBe('orchestrator');
  });

  it('setCurrentIteration', () => {
    const result = executionReducer(undefined, setCurrentIteration(3));
    expect(result.current_iteration).toBe(3);
  });

  it('setGoalValidation', () => {
    const gv = { valid: true, warnings: ['Watch out'] };
    const result = executionReducer(undefined, setGoalValidation(gv));
    expect(result.goal_validation).toEqual(gv);
  });

  it('setProgress', () => {
    const result = executionReducer(undefined, setProgress(75));
    expect(result.progress).toBe(75);
  });

  it('setExecution updates multiple fields at once', () => {
    const patch = { status: 'completed' as const, execution_id: 'e1', progress: 100 };
    const result = executionReducer(undefined, setExecution(patch));
    expect(result.status).toBe('completed');
    expect(result.execution_id).toBe('e1');
    expect(result.progress).toBe(100);
  });

  it('resetExecution restores initial state', () => {
    const modified = {
      ...initial,
      status: 'running' as const,
      execution_id: 'abc',
      progress: 50,
    };
    const result = executionReducer(modified, resetExecution());
    expect(result).toEqual(initial);
  });
});

// ── resultSlice ───────────────────────────────────────────────────────────────
describe('resultSlice', () => {
  const initial = {
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

  it('returns initial state', () => {
    expect(resultReducer(undefined, { type: '' })).toEqual(initial);
  });

  it('setResult stores result data', () => {
    const result = resultReducer(undefined, setResult({ ...initial, summary: 'All done' }));
    expect(result.summary).toBe('All done');
  });

  it('clearResult resets to initial', () => {
    const withData = resultReducer(undefined, setResult({ ...initial, summary: 'Done' }));
    expect(resultReducer(withData, clearResult())).toEqual(initial);
  });
});

// ── lightTestSlice ────────────────────────────────────────────────────────────
describe('lightTestSlice', () => {
  const initial = {
    image: null,
    lights: [],
    camera_view: 'front' as const,
    rendered_result: null,
    analysis_status: 'idle' as const,
    depth_result: null,
    material_result: null,
    analysis_error: null,
  };

  const sampleLight: LightConfig = {
    id: 'light-1',
    type: 'led',
    shape: 'ring',
    position: { x: 0, y: 0, z: 1 },
    intensity: 100,
    color: { r: 255, g: 255, b: 255 },
    polarizer: false,
  };

  it('returns initial state', () => {
    expect(lightTestReducer(undefined, { type: '' })).toEqual(initial);
  });

  it('addLight appends a light config', () => {
    const result = lightTestReducer(undefined, addLight(sampleLight));
    expect(result.lights).toHaveLength(1);
    expect(result.lights[0]).toEqual(sampleLight);
  });

  it('removeLight removes by id', () => {
    const withLight = lightTestReducer(undefined, addLight(sampleLight));
    const result = lightTestReducer(withLight, removeLight('light-1'));
    expect(result.lights).toHaveLength(0);
  });

  it('updateLight patches an existing light', () => {
    const withLight = lightTestReducer(undefined, addLight(sampleLight));
    const result = lightTestReducer(withLight, updateLight({ id: 'light-1', changes: { intensity: 50 } }));
    expect(result.lights[0].intensity).toBe(50);
  });

  it('setCameraView', () => {
    const result = lightTestReducer(undefined, setCameraView('top'));
    expect(result.camera_view).toBe('top');
  });

  it('setRenderedResult', () => {
    const result = lightTestReducer(undefined, setRenderedResult('data:image/png;base64,abc'));
    expect(result.rendered_result).toBe('data:image/png;base64,abc');
  });

  it('setLightTestImage', () => {
    const img: ImageMetadata = {
      id: 'img-1', original_filename: 'test.jpg', label: 'ok', index: 0,
      file_size: 100, upload_timestamp: '2024-01-01T00:00:00Z',
      file_path: '/tmp/test.jpg', group: 'analysis',
    };
    const result = lightTestReducer(undefined, setLightTestImage(img));
    expect(result.image).toEqual(img);
  });

  it('clearLightTest resets to initial', () => {
    const withLight = lightTestReducer(undefined, addLight(sampleLight));
    const result = lightTestReducer(withLight, clearLightTest());
    expect(result).toEqual(initial);
  });

  it('setAnalysisLoading sets analysis_status to loading', () => {
    const result = lightTestReducer(undefined, setAnalysisLoading());
    expect(result.analysis_status).toBe('loading');
  });

  it('setAnalysisLoading clears depth_result and material_result', () => {
    const result = lightTestReducer(undefined, setAnalysisLoading());
    expect(result.depth_result).toBeNull();
    expect(result.material_result).toBeNull();
  });

  it('setAnalysisResult sets analysis_status from payload', () => {
    const result = lightTestReducer(
      undefined,
      setAnalysisResult({
        depth: { status: 'success', depth_stats: null, depth_map_shape: null, depth_map_base64: null, error_message: null },
        material: { status: 'success', surface_type: 'metal', material_map: null, confidence: 0.9, error_message: null },
        status: 'success',
      }),
    );
    expect(result.analysis_status).toBe('success');
  });

  it('setAnalysisResult stores depth_result', () => {
    const depth = { status: 'success' as const, depth_stats: null, depth_map_shape: null, depth_map_base64: null, error_message: null };
    const result = lightTestReducer(
      undefined,
      setAnalysisResult({ depth, material: { status: 'success', surface_type: null, material_map: null, confidence: null, error_message: null }, status: 'success' }),
    );
    expect(result.depth_result).toEqual(depth);
  });

  it('setAnalysisResult stores material_result', () => {
    const material = { status: 'success' as const, surface_type: 'plastic', material_map: null, confidence: 0.75, error_message: null };
    const result = lightTestReducer(
      undefined,
      setAnalysisResult({ depth: { status: 'success', depth_stats: null, depth_map_shape: null, depth_map_base64: null, error_message: null }, material, status: 'success' }),
    );
    expect(result.material_result).toEqual(material);
  });

  it('setAnalysisError sets analysis_status to error', () => {
    const result = lightTestReducer(undefined, setAnalysisError('Connection failed'));
    expect(result.analysis_status).toBe('error');
  });

  it('setAnalysisError stores error message', () => {
    const result = lightTestReducer(undefined, setAnalysisError('Connection failed'));
    expect(result.analysis_error).toBe('Connection failed');
  });

  it('clearAnalysis resets analysis fields to idle/null', () => {
    const withLoading = lightTestReducer(undefined, setAnalysisLoading());
    const result = lightTestReducer(withLoading, clearAnalysis());
    expect(result.analysis_status).toBe('idle');
    expect(result.depth_result).toBeNull();
    expect(result.material_result).toBeNull();
    expect(result.analysis_error).toBeNull();
  });
});

// ── logsSlice ─────────────────────────────────────────────────────────────────
describe('logsSlice', () => {
  const entry: LogEntry = {
    timestamp: '2024-01-01T00:00:00Z',
    agent: 'orchestrator',
    level: 'info',
    message: 'Pipeline started',
  };

  it('returns initial empty array', () => {
    expect(logsReducer(undefined, { type: '' })).toEqual([]);
  });

  it('addLog appends an entry', () => {
    const result = logsReducer(undefined, addLog(entry));
    expect(result).toHaveLength(1);
    expect(result[0]).toEqual(entry);
  });

  it('setLogs replaces entire log array', () => {
    const result = logsReducer([entry], setLogs([{ ...entry, message: 'New message' }]));
    expect(result).toHaveLength(1);
    expect(result[0].message).toBe('New message');
  });

  it('clearLogs empties the array', () => {
    const withLog = logsReducer(undefined, addLog(entry));
    expect(logsReducer(withLog, clearLogs())).toEqual([]);
  });
});
