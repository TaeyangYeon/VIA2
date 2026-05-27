import { renderHook, act } from '@testing-library/react';
import React from 'react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import lightTestReducer, { addLight } from '../store/slices/lightTestSlice';
import { useLightSync } from '../hooks/useLightSync';
import type { LightConfig } from '../services/types';

const makeStore = () =>
  configureStore({ reducer: { light_test: lightTestReducer } });

const makeWrapper =
  (store: ReturnType<typeof makeStore>) =>
  ({ children }: { children: React.ReactNode }) =>
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    React.createElement(Provider as any, { store }, children);

const sampleLight: LightConfig = {
  id: 'light-1',
  type: 'led',
  shape: 'ring',
  position: { x: 0, y: 200, z: 0 },
  intensity: 80,
  color: { r: 255, g: 255, b: 255 },
  polarizer: false,
  pitch: 45,
  yaw: 0,
  lwd: 300,
  size: { width: 50, height: 50 },
};

describe('useLightSync', () => {
  it('returns empty frontViewLights when store has no lights', () => {
    const store = makeStore();
    const { result } = renderHook(() => useLightSync(), { wrapper: makeWrapper(store) });
    expect(result.current.frontViewLights).toHaveLength(0);
  });

  it('returns empty topViewLights when store has no lights', () => {
    const store = makeStore();
    const { result } = renderHook(() => useLightSync(), { wrapper: makeWrapper(store) });
    expect(result.current.topViewLights).toHaveLength(0);
  });

  it('frontViewLights contains one entry per light', () => {
    const store = makeStore();
    act(() => { store.dispatch(addLight(sampleLight)); });
    const { result } = renderHook(() => useLightSync(), { wrapper: makeWrapper(store) });
    expect(result.current.frontViewLights).toHaveLength(1);
  });

  it('topViewLights contains one entry per light', () => {
    const store = makeStore();
    act(() => { store.dispatch(addLight(sampleLight)); });
    const { result } = renderHook(() => useLightSync(), { wrapper: makeWrapper(store) });
    expect(result.current.topViewLights).toHaveLength(1);
  });

  it('frontViewLights includes screenX property', () => {
    const store = makeStore();
    act(() => { store.dispatch(addLight(sampleLight)); });
    const { result } = renderHook(() => useLightSync(), { wrapper: makeWrapper(store) });
    expect(result.current.frontViewLights[0]).toHaveProperty('screenX');
  });

  it('frontViewLights includes screenY property', () => {
    const store = makeStore();
    act(() => { store.dispatch(addLight(sampleLight)); });
    const { result } = renderHook(() => useLightSync(), { wrapper: makeWrapper(store) });
    expect(result.current.frontViewLights[0]).toHaveProperty('screenY');
  });

  it('topViewLights includes screenX property', () => {
    const store = makeStore();
    act(() => { store.dispatch(addLight(sampleLight)); });
    const { result } = renderHook(() => useLightSync(), { wrapper: makeWrapper(store) });
    expect(result.current.topViewLights[0]).toHaveProperty('screenX');
  });

  it('topViewLights includes screenZ property', () => {
    const store = makeStore();
    act(() => { store.dispatch(addLight(sampleLight)); });
    const { result } = renderHook(() => useLightSync(), { wrapper: makeWrapper(store) });
    expect(result.current.topViewLights[0]).toHaveProperty('screenZ');
  });

  it('handleFrontDrag updates x position', () => {
    const store = makeStore();
    act(() => { store.dispatch(addLight(sampleLight)); });
    const { result } = renderHook(() => useLightSync(), { wrapper: makeWrapper(store) });
    act(() => { result.current.handleFrontDrag('light-1', 10, 0); });
    expect(store.getState().light_test.lights[0].position.x).toBe(10);
  });

  it('handleFrontDrag updates y position', () => {
    const store = makeStore();
    act(() => { store.dispatch(addLight(sampleLight)); });
    const { result } = renderHook(() => useLightSync(), { wrapper: makeWrapper(store) });
    act(() => { result.current.handleFrontDrag('light-1', 0, 20); });
    expect(store.getState().light_test.lights[0].position.y).toBe(220);
  });

  it('handleTopDrag updates x position', () => {
    const store = makeStore();
    act(() => { store.dispatch(addLight(sampleLight)); });
    const { result } = renderHook(() => useLightSync(), { wrapper: makeWrapper(store) });
    act(() => { result.current.handleTopDrag('light-1', 10, 0); });
    expect(store.getState().light_test.lights[0].position.x).toBe(10);
  });

  it('handleTopDrag updates z position', () => {
    const store = makeStore();
    act(() => { store.dispatch(addLight(sampleLight)); });
    const { result } = renderHook(() => useLightSync(), { wrapper: makeWrapper(store) });
    act(() => { result.current.handleTopDrag('light-1', 0, 30); });
    expect(store.getState().light_test.lights[0].position.z).toBe(30);
  });

  it('handleFrontDrag and handleTopDrag share x axis', () => {
    const store = makeStore();
    act(() => { store.dispatch(addLight(sampleLight)); });
    const { result } = renderHook(() => useLightSync(), { wrapper: makeWrapper(store) });
    act(() => { result.current.handleFrontDrag('light-1', 5, 0); });
    act(() => { result.current.handleTopDrag('light-1', 3, 0); });
    expect(store.getState().light_test.lights[0].position.x).toBe(8);
  });

  it('handleFrontDrag does nothing when light id not found', () => {
    const store = makeStore();
    act(() => { store.dispatch(addLight(sampleLight)); });
    const { result } = renderHook(() => useLightSync(), { wrapper: makeWrapper(store) });
    const before = store.getState().light_test.lights[0].position;
    act(() => { result.current.handleFrontDrag('nonexistent', 10, 10); });
    expect(store.getState().light_test.lights[0].position).toEqual(before);
  });

  it('handleTopDrag does nothing when light id not found', () => {
    const store = makeStore();
    act(() => { store.dispatch(addLight(sampleLight)); });
    const { result } = renderHook(() => useLightSync(), { wrapper: makeWrapper(store) });
    const before = store.getState().light_test.lights[0].position;
    act(() => { result.current.handleTopDrag('nonexistent', 10, 10); });
    expect(store.getState().light_test.lights[0].position).toEqual(before);
  });

  it('updateLightAngle updates pitch', () => {
    const store = makeStore();
    act(() => { store.dispatch(addLight(sampleLight)); });
    const { result } = renderHook(() => useLightSync(), { wrapper: makeWrapper(store) });
    act(() => { result.current.updateLightAngle('light-1', 'pitch', 30); });
    expect(store.getState().light_test.lights[0].pitch).toBe(30);
  });

  it('updateLightAngle updates yaw', () => {
    const store = makeStore();
    act(() => { store.dispatch(addLight(sampleLight)); });
    const { result } = renderHook(() => useLightSync(), { wrapper: makeWrapper(store) });
    act(() => { result.current.updateLightAngle('light-1', 'yaw', 90); });
    expect(store.getState().light_test.lights[0].yaw).toBe(90);
  });

  it('updateLightLWD updates lwd', () => {
    const store = makeStore();
    act(() => { store.dispatch(addLight(sampleLight)); });
    const { result } = renderHook(() => useLightSync(), { wrapper: makeWrapper(store) });
    act(() => { result.current.updateLightLWD('light-1', 500); });
    expect(store.getState().light_test.lights[0].lwd).toBe(500);
  });

  it('exposes handleFrontDrag function', () => {
    const store = makeStore();
    const { result } = renderHook(() => useLightSync(), { wrapper: makeWrapper(store) });
    expect(typeof result.current.handleFrontDrag).toBe('function');
  });

  it('exposes handleTopDrag function', () => {
    const store = makeStore();
    const { result } = renderHook(() => useLightSync(), { wrapper: makeWrapper(store) });
    expect(typeof result.current.handleTopDrag).toBe('function');
  });

  it('exposes updateLightAngle function', () => {
    const store = makeStore();
    const { result } = renderHook(() => useLightSync(), { wrapper: makeWrapper(store) });
    expect(typeof result.current.updateLightAngle).toBe('function');
  });

  it('exposes updateLightLWD function', () => {
    const store = makeStore();
    const { result } = renderHook(() => useLightSync(), { wrapper: makeWrapper(store) });
    expect(typeof result.current.updateLightLWD).toBe('function');
  });

  it('screenX is a number between 0 and 1 for centered light', () => {
    const store = makeStore();
    act(() => { store.dispatch(addLight({ ...sampleLight, position: { x: 0, y: 0, z: 0 } })); });
    const { result } = renderHook(() => useLightSync(), { wrapper: makeWrapper(store) });
    const { screenX } = result.current.frontViewLights[0];
    expect(typeof screenX).toBe('number');
    expect(screenX).toBeGreaterThanOrEqual(0);
    expect(screenX).toBeLessThanOrEqual(1);
  });
});
