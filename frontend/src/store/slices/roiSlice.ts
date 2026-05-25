import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { ROICoordinates } from '../../services/types';

type RoiState = ROICoordinates | null;

const roiSlice = createSlice({
  name: 'roi',
  initialState: null as RoiState,
  reducers: {
    setRoi(_state, action: PayloadAction<ROICoordinates>) {
      return action.payload;
    },
    clearRoi() {
      return null;
    },
  },
});

export const { setRoi, clearRoi } = roiSlice.actions;
export default roiSlice.reducer;
