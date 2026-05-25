import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { InspectionConfig } from '../../services/types';

const initialState: InspectionConfig = {
  mode: 'inspection',
  max_iteration: 3,
  success_criteria: {
    accuracy: null,
    fp_rate: null,
    fn_rate: null,
    coord_error: null,
  },
};

const configSlice = createSlice({
  name: 'config',
  initialState,
  reducers: {
    setConfig(_state, action: PayloadAction<InspectionConfig>) {
      return action.payload;
    },
  },
});

export const { setConfig } = configSlice.actions;
export default configSlice.reducer;
