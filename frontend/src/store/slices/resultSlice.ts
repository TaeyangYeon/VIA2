import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { ExecutionResult } from '../../services/types';

const initialState: ExecutionResult = {
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

const resultSlice = createSlice({
  name: 'result',
  initialState,
  reducers: {
    setResult(_state, action: PayloadAction<ExecutionResult>) {
      return action.payload;
    },
    clearResult() {
      return initialState;
    },
  },
});

export const { setResult, clearResult } = resultSlice.actions;
export default resultSlice.reducer;
