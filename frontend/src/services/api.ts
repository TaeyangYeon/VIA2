import axios from 'axios';
import type {
  EngineSettings,
  ImageMetadata,
  ROICoordinates,
  InspectionConfig,
  ConfigSaveResponse,
  AgentDirectives,
  ExecuteRequest,
  ExecutionStatus,
  LogsResponse,
} from './types';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
});

// ── Health ────────────────────────────────────────────────────────────────────
export const getHealth = (): Promise<{ status: string; version: string }> =>
  apiClient.get('/health').then(r => r.data);

// ── Engine ────────────────────────────────────────────────────────────────────
export const getEngine = (): Promise<EngineSettings> =>
  apiClient.get('/api/engine').then(r => r.data);

export const updateEngine = (settings: EngineSettings): Promise<EngineSettings> =>
  apiClient.post('/api/engine', settings).then(r => r.data);

// ── Images ────────────────────────────────────────────────────────────────────
export const uploadImage = (file: File): Promise<ImageMetadata> => {
  const form = new FormData();
  form.append('file', file);
  return apiClient
    .post('/api/images/upload', form, { headers: { 'Content-Type': 'multipart/form-data' } })
    .then(r => r.data);
};

export const getImages = (group?: string): Promise<ImageMetadata[]> =>
  apiClient.get('/api/images', { params: group ? { group } : {} }).then(r => r.data);

export const clearAllImages = (): Promise<{ message: string }> =>
  apiClient.delete('/api/images').then(r => r.data);

export const getImageById = (id: string): Promise<ImageMetadata> =>
  apiClient.get(`/api/images/${id}`).then(r => r.data);

export const deleteImage = (id: string): Promise<{ message: string }> =>
  apiClient.delete(`/api/images/${id}`).then(r => r.data);

// ── ROI ───────────────────────────────────────────────────────────────────────
export const getRoi = (): Promise<ROICoordinates | null> =>
  apiClient.get('/api/roi').then(r => r.data);

export const setRoi = (roi: ROICoordinates): Promise<ROICoordinates> =>
  apiClient.post('/api/roi', roi).then(r => r.data);

export const clearRoi = (): Promise<{ message: string }> =>
  apiClient.delete('/api/roi').then(r => r.data);

// ── Config ────────────────────────────────────────────────────────────────────
export const getConfig = (): Promise<InspectionConfig> =>
  apiClient.get('/api/config').then(r => r.data);

export const saveConfig = (config: InspectionConfig): Promise<ConfigSaveResponse> =>
  apiClient.post('/api/config', config).then(r => r.data);

// ── Directives ────────────────────────────────────────────────────────────────
export const getDirectives = (): Promise<AgentDirectives> =>
  apiClient.get('/api/directives').then(r => r.data);

export const saveDirectives = (directives: AgentDirectives): Promise<AgentDirectives> =>
  apiClient.post('/api/directives', directives).then(r => r.data);

// ── Execution ─────────────────────────────────────────────────────────────────
export const startExecution = (
  req: ExecuteRequest,
): Promise<{ execution_id: string; status: string }> =>
  apiClient.post('/api/execute', req).then(r => r.data);

export const listExecutions = (): Promise<ExecutionStatus[]> =>
  apiClient.get('/api/execute').then(r => r.data);

export const getExecution = (id: string): Promise<ExecutionStatus> =>
  apiClient.get(`/api/execute/${id}`).then(r => r.data);

export const cancelExecution = (
  id: string,
): Promise<{ message: string; execution_id: string }> =>
  apiClient.delete(`/api/execute/${id}`).then(r => r.data);

// ── Logs ──────────────────────────────────────────────────────────────────────
export const getLogAgents = (): Promise<{ agents: string[] }> =>
  apiClient.get('/api/logs/agents').then(r => r.data);

export const getLogs = (params?: {
  agent_name?: string;
  level?: string;
  limit?: number;
}): Promise<LogsResponse> =>
  apiClient.get('/api/logs', { params: params ?? {} }).then(r => r.data);

export const clearLogs = (): Promise<{ cleared: boolean }> =>
  apiClient.delete('/api/logs').then(r => r.data);

export default apiClient;
