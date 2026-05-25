import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { ImageMetadata } from '../../services/types';

interface ImagesState {
  analysis: ImageMetadata[];
  test: ImageMetadata[];
}

const initialState: ImagesState = {
  analysis: [],
  test: [],
};

const imagesSlice = createSlice({
  name: 'images',
  initialState,
  reducers: {
    addImage(state, action: PayloadAction<ImageMetadata>) {
      const img = action.payload;
      if (img.group === 'test') {
        state.test.push(img);
      } else {
        state.analysis.push(img);
      }
    },
    setAnalysisImages(state, action: PayloadAction<ImageMetadata[]>) {
      state.analysis = action.payload;
    },
    setTestImages(state, action: PayloadAction<ImageMetadata[]>) {
      state.test = action.payload;
    },
    removeImage(state, action: PayloadAction<string>) {
      const id = action.payload;
      state.analysis = state.analysis.filter(img => img.id !== id);
      state.test = state.test.filter(img => img.id !== id);
    },
    clearImages() {
      return initialState;
    },
  },
});

export const { addImage, setAnalysisImages, setTestImages, removeImage, clearImages } =
  imagesSlice.actions;
export default imagesSlice.reducer;
