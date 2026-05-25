import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { LogEntry } from '../../services/types';

const logsSlice = createSlice({
  name: 'logs',
  initialState: [] as LogEntry[],
  reducers: {
    addLog(state, action: PayloadAction<LogEntry>) {
      state.push(action.payload);
    },
    setLogs(_state, action: PayloadAction<LogEntry[]>) {
      return action.payload;
    },
    clearLogs() {
      return [];
    },
  },
});

export const { addLog, setLogs, clearLogs } = logsSlice.actions;
export default logsSlice.reducer;
