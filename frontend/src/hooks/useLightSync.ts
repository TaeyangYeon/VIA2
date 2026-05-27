import { useAppDispatch, useAppSelector } from '../store';
import { updateLight } from '../store/slices/lightTestSlice';
import type { LightConfig } from '../services/types';

export interface FrontViewLight extends LightConfig {
  screenX: number;
  screenY: number;
}

export interface TopViewLight extends LightConfig {
  screenX: number;
  screenZ: number;
}

const COORD_RANGE = 1000;

function worldToScreen(world: number): number {
  return Math.max(0.05, Math.min(0.95, (world + COORD_RANGE / 2) / COORD_RANGE));
}

export function useLightSync() {
  const dispatch = useAppDispatch();
  const lights = useAppSelector(s => s.light_test.lights);

  const frontViewLights: FrontViewLight[] = lights.map(l => ({
    ...l,
    screenX: worldToScreen(l.position.x),
    screenY: 1 - worldToScreen(l.position.y),
  }));

  const topViewLights: TopViewLight[] = lights.map(l => ({
    ...l,
    screenX: worldToScreen(l.position.x),
    screenZ: worldToScreen(l.position.z),
  }));

  const handleFrontDrag = (lightId: string, deltaX: number, deltaY: number) => {
    const light = lights.find(l => l.id === lightId);
    if (!light) return;
    dispatch(
      updateLight({
        id: lightId,
        changes: {
          position: {
            ...light.position,
            x: light.position.x + deltaX,
            y: light.position.y + deltaY,
          },
        },
      }),
    );
  };

  const handleTopDrag = (lightId: string, deltaX: number, deltaZ: number) => {
    const light = lights.find(l => l.id === lightId);
    if (!light) return;
    dispatch(
      updateLight({
        id: lightId,
        changes: {
          position: {
            ...light.position,
            x: light.position.x + deltaX,
            z: light.position.z + deltaZ,
          },
        },
      }),
    );
  };

  const updateLightAngle = (id: string, field: 'pitch' | 'yaw', value: number) => {
    dispatch(updateLight({ id, changes: { [field]: value } }));
  };

  const updateLightLWD = (id: string, value: number) => {
    dispatch(updateLight({ id, changes: { lwd: value } }));
  };

  return {
    frontViewLights,
    topViewLights,
    handleFrontDrag,
    handleTopDrag,
    updateLightAngle,
    updateLightLWD,
  };
}
