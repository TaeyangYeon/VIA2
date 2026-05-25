import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { ProjectState } from '../../services/types';

const initialState: ProjectState = {
  name: '',
  created_at: '',
};

const projectSlice = createSlice({
  name: 'project',
  initialState,
  reducers: {
    setProject(state, action: PayloadAction<ProjectState>) {
      state.name = action.payload.name;
      state.created_at = action.payload.created_at;
    },
  },
});

export const { setProject } = projectSlice.actions;
export default projectSlice.reducer;
