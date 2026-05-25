import { configureStore } from '@reduxjs/toolkit';
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux';

import projectReducer from './slices/projectSlice';
import engineReducer from './slices/engineSlice';
import imagesReducer from './slices/imagesSlice';
import roiReducer from './slices/roiSlice';
import configReducer from './slices/configSlice';
import directivesReducer from './slices/directivesSlice';
import executionReducer from './slices/executionSlice';
import resultReducer from './slices/resultSlice';
import lightTestReducer from './slices/lightTestSlice';
import logsReducer from './slices/logsSlice';

export const store = configureStore({
  reducer: {
    project: projectReducer,
    engine: engineReducer,
    images: imagesReducer,
    roi: roiReducer,
    config: configReducer,
    directives: directivesReducer,
    execution: executionReducer,
    result: resultReducer,
    light_test: lightTestReducer,
    logs: logsReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export const useAppDispatch = (): AppDispatch => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
