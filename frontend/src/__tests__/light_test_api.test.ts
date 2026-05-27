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
import * as lightTestApi from '../services/light_test_api';
import type { LightTestAnalysisResponse } from '../services/light_test_api';

const mockAxiosCreate = axios.create as jest.Mock;
const mockInstance = mockAxiosCreate.mock.results[0]?.value ?? mockAxiosCreate();

const mockResponse: LightTestAnalysisResponse = {
  status: 'success',
  depth: {
    status: 'success',
    depth_stats: {
      depth_complexity: 0.5,
      has_shadow_region: true,
      depth_range: 0.8,
      depth_mean: 0.4,
      depth_gradient_max: 0.35,
    },
    depth_map_shape: [100, 100],
    depth_map_base64: 'abc123base64',
    error_message: null,
  },
  material: {
    status: 'success',
    surface_type: 'metal',
    material_map: null,
    confidence: 0.85,
    error_message: null,
  },
};

describe('light_test_api — module exports', () => {
  it('exports analyzeLightTestImage as a function', () => {
    expect(typeof lightTestApi.analyzeLightTestImage).toBe('function');
  });
});

describe('light_test_api — axios instance', () => {
  it('creates axios instance with baseURL http://localhost:8000', () => {
    expect(mockAxiosCreate).toHaveBeenCalledWith(
      expect.objectContaining({ baseURL: 'http://localhost:8000' }),
    );
  });
});

describe('analyzeLightTestImage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (mockInstance.post as jest.Mock).mockResolvedValue({ data: mockResponse });
  });

  it('calls POST /api/light_test/analyze', async () => {
    const file = new File(['img'], 'test.png', { type: 'image/png' });
    await lightTestApi.analyzeLightTestImage(file);
    expect(mockInstance.post).toHaveBeenCalledWith(
      '/api/light_test/analyze',
      expect.any(FormData),
      expect.objectContaining({ headers: expect.objectContaining({ 'Content-Type': 'multipart/form-data' }) }),
    );
  });

  it('appends file to FormData with key "file"', async () => {
    const file = new File(['img'], 'test.png', { type: 'image/png' });
    await lightTestApi.analyzeLightTestImage(file);
    const [, formData] = (mockInstance.post as jest.Mock).mock.calls[0];
    expect(formData).toBeInstanceOf(FormData);
    expect(formData.get('file')).toBe(file);
  });

  it('returns response.data from axios', async () => {
    const file = new File(['img'], 'test.png', { type: 'image/png' });
    const result = await lightTestApi.analyzeLightTestImage(file);
    expect(result).toEqual(mockResponse);
  });

  it('uses multipart/form-data content type header', async () => {
    const file = new File(['img'], 'test.png', { type: 'image/png' });
    await lightTestApi.analyzeLightTestImage(file);
    const [, , config] = (mockInstance.post as jest.Mock).mock.calls[0];
    expect(config.headers['Content-Type']).toBe('multipart/form-data');
  });

  it('propagates axios errors to the caller', async () => {
    (mockInstance.post as jest.Mock).mockRejectedValue(new Error('Network error'));
    const file = new File(['img'], 'test.png', { type: 'image/png' });
    await expect(lightTestApi.analyzeLightTestImage(file)).rejects.toThrow('Network error');
  });

  it('returned status is "success" when both agents succeed', async () => {
    const file = new File(['img'], 'test.png', { type: 'image/png' });
    const result = await lightTestApi.analyzeLightTestImage(file);
    expect(result.status).toBe('success');
  });

  it('returned depth has depth_map_base64 field', async () => {
    const file = new File(['img'], 'test.png', { type: 'image/png' });
    const result = await lightTestApi.analyzeLightTestImage(file);
    expect('depth_map_base64' in result.depth).toBe(true);
  });

  it('returned material has surface_type field', async () => {
    const file = new File(['img'], 'test.png', { type: 'image/png' });
    const result = await lightTestApi.analyzeLightTestImage(file);
    expect('surface_type' in result.material).toBe(true);
  });
});
