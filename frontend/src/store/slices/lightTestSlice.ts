import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { ImageMetadata, LightConfig } from '../../services/types';
import type { DepthAnalysisResult, MaterialAnalysisResult } from '../../services/light_test_api';

interface LightTestState {
  image: ImageMetadata | null;
  lights: LightConfig[];
  camera_view: 'front' | 'top';
  rendered_result: string | null;
  analysis_status: 'idle' | 'loading' | 'success' | 'partial' | 'error';
  depth_result: DepthAnalysisResult | null;
  material_result: MaterialAnalysisResult | null;
  analysis_error: string | null;
  selected_light_id: string | null;
  lens_polarizer_angle: number;
  is_grayscale: boolean;
}

const initialState: LightTestState = {
  image: null,
  lights: [],
  camera_view: 'front',
  rendered_result: null,
  analysis_status: 'idle',
  depth_result: null,
  material_result: null,
  analysis_error: null,
  selected_light_id: null,
  lens_polarizer_angle: 0,
  is_grayscale: false,
};

const lightTestSlice = createSlice({
  name: 'light_test',
  initialState,
  reducers: {
    setLightTestImage(state, action: PayloadAction<ImageMetadata | null>) {
      state.image = action.payload;
    },
    addLight(state, action: PayloadAction<LightConfig>) {
      state.lights.push(action.payload);
    },
    removeLight(state, action: PayloadAction<string>) {
      state.lights = state.lights.filter(l => l.id !== action.payload);
    },
    updateLight(
      state,
      action: PayloadAction<{ id: string; changes: Partial<LightConfig> }>,
    ) {
      const idx = state.lights.findIndex(l => l.id === action.payload.id);
      if (idx !== -1) {
        state.lights[idx] = { ...state.lights[idx], ...action.payload.changes };
      }
    },
    setCameraView(state, action: PayloadAction<'front' | 'top'>) {
      state.camera_view = action.payload;
    },
    setRenderedResult(state, action: PayloadAction<string | null>) {
      state.rendered_result = action.payload;
    },
    setAnalysisLoading(state) {
      state.analysis_status = 'loading';
      state.depth_result = null;
      state.material_result = null;
      state.analysis_error = null;
    },
    setAnalysisResult(
      state,
      action: PayloadAction<{
        depth: DepthAnalysisResult;
        material: MaterialAnalysisResult;
        status: string;
      }>,
    ) {
      const s = action.payload.status;
      state.analysis_status =
        s === 'success' || s === 'partial' || s === 'error' ? s : 'error';
      state.depth_result = action.payload.depth;
      state.material_result = action.payload.material;
      state.analysis_error = null;
    },
    setAnalysisError(state, action: PayloadAction<string>) {
      state.analysis_status = 'error';
      state.analysis_error = action.payload;
    },
    clearAnalysis(state) {
      state.analysis_status = 'idle';
      state.depth_result = null;
      state.material_result = null;
      state.analysis_error = null;
    },
    selectLight(state, action: PayloadAction<string | null>) {
      state.selected_light_id = action.payload;
    },
    setLensPolarizer(state, action: PayloadAction<number>) {
      state.lens_polarizer_angle = action.payload;
    },
    setIsGrayscale(state, action: PayloadAction<boolean>) {
      state.is_grayscale = action.payload;
    },
    clearLightTest() {
      return initialState;
    },
  },
});

export const {
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
  selectLight,
  setLensPolarizer,
  setIsGrayscale,
  clearLightTest,
} = lightTestSlice.actions;
export default lightTestSlice.reducer;
