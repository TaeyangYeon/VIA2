// ── Backend model types ───────────────────────────────────────────────────────
// Mirrors backend/models/engine.py :: EngineSettings
export interface EngineSettings {
  mode: 'local' | 'remote';
  local_ollama_url: string;
  remote_url: string | null;
  remote_type: string;
  remote_auth_token: string | null;
  model_name: string;
}

// Mirrors backend/models/image.py :: ImageMetadata
export interface ImageMetadata {
  id: string;
  original_filename: string;
  label: string;
  index: number;
  file_size: number;
  upload_timestamp: string;
  file_path: string;
  group: string;
}

// Mirrors backend/models/roi.py :: ROICoordinates
export interface ROICoordinates {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

// Mirrors backend/models/config.py :: SuccessCriteria + InspectionConfig
export interface SuccessCriteria {
  accuracy: number | null;
  fp_rate: number | null;
  fn_rate: number | null;
  coord_error: number | null;
}

export interface InspectionConfig {
  mode: 'inspection' | 'align';
  max_iteration: number;
  success_criteria: SuccessCriteria;
}

export interface ConfigSaveResponse extends InspectionConfig {
  warnings: string[];
}

// Mirrors backend/models/directives.py :: AgentDirectives
export interface AgentDirectives {
  orchestrator: string;
  spec: string;
  image_analysis: string;
  depth: string;
  material: string;
  pipeline_composer: string;
  vision_judge: string;
  inspection_plan: string;
  test: string;
}

// ── Execution types ───────────────────────────────────────────────────────────
export interface ExecuteRequest {
  user_text: string;
}

export interface GoalValidation {
  valid: boolean;
  warnings: string[];
}

export interface ExecutionResult {
  summary: string | null;
  pipeline: object | null;
  inspection_plan: object | null;
  blueprint_svg: string | null;
  parameter_sheet: object | null;
  metrics: object | null;
  item_results: object[] | null;
  lighting_suggestions: string[] | null;
  improvement_suggestions: string[] | null;
  decision: string | null;
  decision_reason: string | null;
}

export interface ExecutionStatus {
  execution_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  current_agent: string | null;
  current_iteration: number;
  goal_validation: GoalValidation | null;
  progress: number;
  result?: ExecutionResult;
}

// ── Log types ─────────────────────────────────────────────────────────────────
export interface LogEntry {
  timestamp: string;
  agent: string;
  level: 'info' | 'warn' | 'error';
  message: string;
}

export interface LogsResponse {
  logs: LogEntry[];
  total: number;
}

// ── Light test types (frontend-only) ─────────────────────────────────────────
export interface LightPosition {
  x: number;
  y: number;
  z: number;
}

export interface LightColor {
  r: number;
  g: number;
  b: number;
}

export interface LightSize {
  width: number;
  height: number;
}

export interface LightConfig {
  id: string;
  type: 'led' | 'halogen' | 'uv' | 'ir';
  shape: 'ring' | 'bar' | 'spot' | 'coaxial' | 'dome' | 'low_angle_ring';
  position: LightPosition;
  intensity: number;
  color: LightColor;
  polarizer: boolean;
  polarizer_enabled?: boolean;
  polarizer_angle?: number;
  pitch?: number;
  yaw?: number;
  lwd?: number;
  size?: LightSize;
}

// ── Project type (frontend-only) ──────────────────────────────────────────────
export interface ProjectState {
  name: string;
  created_at: string;
}
