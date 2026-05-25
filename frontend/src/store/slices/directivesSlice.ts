import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { AgentDirectives } from '../../services/types';

const initialState: AgentDirectives = {
  orchestrator: '',
  spec: '',
  image_analysis: '',
  depth: '',
  material: '',
  pipeline_composer: '',
  vision_judge: '',
  inspection_plan: '',
  test: '',
};

const directivesSlice = createSlice({
  name: 'directives',
  initialState,
  reducers: {
    setDirectives(_state, action: PayloadAction<AgentDirectives>) {
      return action.payload;
    },
    updateDirective(
      state,
      action: PayloadAction<{ key: keyof AgentDirectives; value: string }>,
    ) {
      state[action.payload.key] = action.payload.value;
    },
  },
});

export const { setDirectives, updateDirective } = directivesSlice.actions;
export default directivesSlice.reducer;
