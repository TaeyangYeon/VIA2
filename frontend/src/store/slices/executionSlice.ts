import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { GoalValidation } from '../../services/types';

type ExecutionStatus = 'idle' | 'running' | 'completed' | 'failed' | 'cancelled';

interface ExecutionState {
  status: ExecutionStatus;
  execution_id: string | null;
  current_agent: string | null;
  current_iteration: number;
  goal_validation: GoalValidation | null;
  progress: number;
}

const initialState: ExecutionState = {
  status: 'idle',
  execution_id: null,
  current_agent: null,
  current_iteration: 0,
  goal_validation: null,
  progress: 0,
};

const executionSlice = createSlice({
  name: 'execution',
  initialState,
  reducers: {
    setExecutionStatus(state, action: PayloadAction<ExecutionStatus>) {
      state.status = action.payload;
    },
    setExecutionId(state, action: PayloadAction<string | null>) {
      state.execution_id = action.payload;
    },
    setCurrentAgent(state, action: PayloadAction<string | null>) {
      state.current_agent = action.payload;
    },
    setCurrentIteration(state, action: PayloadAction<number>) {
      state.current_iteration = action.payload;
    },
    setGoalValidation(state, action: PayloadAction<GoalValidation | null>) {
      state.goal_validation = action.payload;
    },
    setProgress(state, action: PayloadAction<number>) {
      state.progress = action.payload;
    },
    setExecution(state, action: PayloadAction<Partial<ExecutionState>>) {
      return { ...state, ...action.payload };
    },
    resetExecution() {
      return initialState;
    },
  },
});

export const {
  setExecutionStatus,
  setExecutionId,
  setCurrentAgent,
  setCurrentIteration,
  setGoalValidation,
  setProgress,
  setExecution,
  resetExecution,
} = executionSlice.actions;
export default executionSlice.reducer;
