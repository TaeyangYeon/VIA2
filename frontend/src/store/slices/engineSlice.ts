import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { EngineSettings } from '../../services/types';

const initialState: EngineSettings = {
  mode: 'local',
  local_ollama_url: 'http://127.0.0.1:11434',
  remote_url: null,
  remote_type: 'colab',
  remote_auth_token: null,
  model_name: 'qwen2.5-coder:7b',
};

const engineSlice = createSlice({
  name: 'engine',
  initialState,
  reducers: {
    setEngine(_state, action: PayloadAction<EngineSettings>) {
      return action.payload;
    },
  },
});

export const { setEngine } = engineSlice.actions;
export default engineSlice.reducer;
