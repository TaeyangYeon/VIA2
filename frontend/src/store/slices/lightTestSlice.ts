import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { ImageMetadata, LightConfig } from '../../services/types';

interface LightTestState {
  image: ImageMetadata | null;
  lights: LightConfig[];
  camera_view: 'front' | 'top';
  rendered_result: string | null;
}

const initialState: LightTestState = {
  image: null,
  lights: [],
  camera_view: 'front',
  rendered_result: null,
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
  clearLightTest,
} = lightTestSlice.actions;
export default lightTestSlice.reducer;
