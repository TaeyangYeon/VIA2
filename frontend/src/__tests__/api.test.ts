jest.mock('axios', () => {
  const mockInstance = {
    get: jest.fn().mockResolvedValue({ data: {} }),
    post: jest.fn().mockResolvedValue({ data: {} }),
    delete: jest.fn().mockResolvedValue({ data: {} }),
  };
  return {
    __esModule: true,
    default: {
      create: jest.fn(() => mockInstance),
    },
    create: jest.fn(() => mockInstance),
  };
});

import axios from 'axios';
import * as api from '../services/api';

const mockAxiosCreate = axios.create as jest.Mock;
const mockInstance = mockAxiosCreate.mock.results[0]?.value ?? mockAxiosCreate();

describe('API client — axios instance', () => {
  it('axios.create is called with baseURL http://localhost:8000', () => {
    expect(mockAxiosCreate).toHaveBeenCalledWith(
      expect.objectContaining({ baseURL: 'http://localhost:8000' }),
    );
  });
});

describe('API client — function exports', () => {
  it('exports getHealth', () => expect(typeof api.getHealth).toBe('function'));
  it('exports getEngine', () => expect(typeof api.getEngine).toBe('function'));
  it('exports updateEngine', () => expect(typeof api.updateEngine).toBe('function'));
  it('exports uploadImage', () => expect(typeof api.uploadImage).toBe('function'));
  it('exports getImages', () => expect(typeof api.getImages).toBe('function'));
  it('exports clearAllImages', () => expect(typeof api.clearAllImages).toBe('function'));
  it('exports getImageById', () => expect(typeof api.getImageById).toBe('function'));
  it('exports deleteImage', () => expect(typeof api.deleteImage).toBe('function'));
  it('exports getRoi', () => expect(typeof api.getRoi).toBe('function'));
  it('exports setRoi', () => expect(typeof api.setRoi).toBe('function'));
  it('exports clearRoi', () => expect(typeof api.clearRoi).toBe('function'));
  it('exports getConfig', () => expect(typeof api.getConfig).toBe('function'));
  it('exports saveConfig', () => expect(typeof api.saveConfig).toBe('function'));
  it('exports getDirectives', () => expect(typeof api.getDirectives).toBe('function'));
  it('exports saveDirectives', () => expect(typeof api.saveDirectives).toBe('function'));
  it('exports startExecution', () => expect(typeof api.startExecution).toBe('function'));
  it('exports listExecutions', () => expect(typeof api.listExecutions).toBe('function'));
  it('exports getExecution', () => expect(typeof api.getExecution).toBe('function'));
  it('exports cancelExecution', () => expect(typeof api.cancelExecution).toBe('function'));
  it('exports getLogAgents', () => expect(typeof api.getLogAgents).toBe('function'));
  it('exports getLogs', () => expect(typeof api.getLogs).toBe('function'));
  it('exports clearLogs', () => expect(typeof api.clearLogs).toBe('function'));
});

describe('API client — endpoint calls', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockInstance.get.mockResolvedValue({ data: {} });
    mockInstance.post.mockResolvedValue({ data: {} });
    mockInstance.delete.mockResolvedValue({ data: {} });
  });

  it('getHealth calls GET /health', async () => {
    await api.getHealth();
    expect(mockInstance.get).toHaveBeenCalledWith('/health');
  });

  it('getEngine calls GET /api/engine', async () => {
    await api.getEngine();
    expect(mockInstance.get).toHaveBeenCalledWith('/api/engine');
  });

  it('updateEngine calls POST /api/engine', async () => {
    const settings = {
      mode: 'local' as const,
      local_ollama_url: 'http://127.0.0.1:11434',
      remote_url: null,
      remote_type: 'colab',
      remote_auth_token: null,
      model_name: 'qwen2.5-coder:7b',
    };
    await api.updateEngine(settings);
    expect(mockInstance.post).toHaveBeenCalledWith('/api/engine', settings);
  });

  it('getImages calls GET /api/images without params', async () => {
    await api.getImages();
    expect(mockInstance.get).toHaveBeenCalledWith('/api/images', expect.anything());
  });

  it('getImages calls GET /api/images with group param', async () => {
    await api.getImages('analysis');
    expect(mockInstance.get).toHaveBeenCalledWith(
      '/api/images',
      expect.objectContaining({ params: expect.objectContaining({ group: 'analysis' }) }),
    );
  });

  it('clearAllImages calls DELETE /api/images', async () => {
    await api.clearAllImages();
    expect(mockInstance.delete).toHaveBeenCalledWith('/api/images');
  });

  it('getImageById calls GET /api/images/:id', async () => {
    await api.getImageById('img-123');
    expect(mockInstance.get).toHaveBeenCalledWith('/api/images/img-123');
  });

  it('deleteImage calls DELETE /api/images/:id', async () => {
    await api.deleteImage('img-123');
    expect(mockInstance.delete).toHaveBeenCalledWith('/api/images/img-123');
  });

  it('getRoi calls GET /api/roi', async () => {
    await api.getRoi();
    expect(mockInstance.get).toHaveBeenCalledWith('/api/roi');
  });

  it('setRoi calls POST /api/roi', async () => {
    const roi = { x1: 0, y1: 0, x2: 100, y2: 100 };
    await api.setRoi(roi);
    expect(mockInstance.post).toHaveBeenCalledWith('/api/roi', roi);
  });

  it('clearRoi calls DELETE /api/roi', async () => {
    await api.clearRoi();
    expect(mockInstance.delete).toHaveBeenCalledWith('/api/roi');
  });

  it('getConfig calls GET /api/config', async () => {
    await api.getConfig();
    expect(mockInstance.get).toHaveBeenCalledWith('/api/config');
  });

  it('saveConfig calls POST /api/config', async () => {
    const config = {
      mode: 'inspection' as const,
      max_iteration: 3,
      success_criteria: { accuracy: null, fp_rate: null, fn_rate: null, coord_error: null },
    };
    await api.saveConfig(config);
    expect(mockInstance.post).toHaveBeenCalledWith('/api/config', config);
  });

  it('getDirectives calls GET /api/directives', async () => {
    await api.getDirectives();
    expect(mockInstance.get).toHaveBeenCalledWith('/api/directives');
  });

  it('saveDirectives calls POST /api/directives', async () => {
    const directives = {
      orchestrator: '', spec: '', image_analysis: '', depth: '',
      material: '', pipeline_composer: '', vision_judge: '', inspection_plan: '', test: '',
    };
    await api.saveDirectives(directives);
    expect(mockInstance.post).toHaveBeenCalledWith('/api/directives', directives);
  });

  it('startExecution calls POST /api/execute', async () => {
    await api.startExecution({ user_text: 'Detect defects' });
    expect(mockInstance.post).toHaveBeenCalledWith('/api/execute', { user_text: 'Detect defects' });
  });

  it('listExecutions calls GET /api/execute', async () => {
    await api.listExecutions();
    expect(mockInstance.get).toHaveBeenCalledWith('/api/execute');
  });

  it('getExecution calls GET /api/execute/:id', async () => {
    await api.getExecution('exec-123');
    expect(mockInstance.get).toHaveBeenCalledWith('/api/execute/exec-123');
  });

  it('cancelExecution calls DELETE /api/execute/:id', async () => {
    await api.cancelExecution('exec-123');
    expect(mockInstance.delete).toHaveBeenCalledWith('/api/execute/exec-123');
  });

  it('getLogAgents calls GET /api/logs/agents', async () => {
    await api.getLogAgents();
    expect(mockInstance.get).toHaveBeenCalledWith('/api/logs/agents');
  });

  it('getLogs calls GET /api/logs', async () => {
    await api.getLogs();
    expect(mockInstance.get).toHaveBeenCalledWith('/api/logs', expect.anything());
  });

  it('getLogs passes query params', async () => {
    await api.getLogs({ agent_name: 'orchestrator', level: 'info', limit: 50 });
    expect(mockInstance.get).toHaveBeenCalledWith(
      '/api/logs',
      expect.objectContaining({
        params: expect.objectContaining({ agent_name: 'orchestrator', level: 'info', limit: 50 }),
      }),
    );
  });

  it('clearLogs calls DELETE /api/logs', async () => {
    await api.clearLogs();
    expect(mockInstance.delete).toHaveBeenCalledWith('/api/logs');
  });
});
