import { Plus, Trash2 } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../../store';
import {
  addLight,
  removeLight,
  updateLight,
  selectLight,
} from '../../store/slices/lightTestSlice';
import type { LightConfig } from '../../services/types';

function makeDefaultLight(): LightConfig {
  return {
    id: Date.now().toString(),
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
}

const SHAPE_OPTIONS: LightConfig['shape'][] = [
  'ring', 'bar', 'spot', 'coaxial', 'dome', 'low_angle_ring',
];

const TYPE_OPTIONS: LightConfig['type'][] = ['led', 'halogen', 'uv', 'ir'];

const SHAPE_LABELS: Record<LightConfig['shape'], string> = {
  ring: 'Ring',
  bar: 'Bar',
  spot: 'Spot',
  coaxial: 'Coaxial',
  dome: 'Dome',
  low_angle_ring: 'Low-angle Ring',
};

const TYPE_LABELS: Record<LightConfig['type'], string> = {
  led: 'LED',
  halogen: 'Halogen',
  uv: 'UV',
  ir: 'IR',
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  background: 'rgba(255,255,255,0.05)',
  border: '1px solid #2a2a2a',
  borderRadius: 4,
  color: '#f5f5f5',
  padding: '3px 6px',
  fontSize: '0.75rem',
  outline: 'none',
  transition: 'all 150ms ease-in-out',
};

const labelStyle: React.CSSProperties = {
  color: '#555555',
  fontSize: '0.65rem',
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
  marginBottom: 2,
};

export default function LightController() {
  const dispatch = useAppDispatch();
  const lights = useAppSelector(s => s.light_test.lights);
  const selected_light_id = useAppSelector(s => s.light_test.selected_light_id);
  const material_result = useAppSelector(s => s.light_test.material_result);

  const selectedLight = lights.find(l => l.id === selected_light_id) ?? null;

  const handleAddLight = () => {
    const newLight = makeDefaultLight();
    dispatch(addLight(newLight));
    dispatch(selectLight(newLight.id));
  };

  const handleRemoveLight = () => {
    if (!selected_light_id) return;
    dispatch(removeLight(selected_light_id));
    dispatch(selectLight(null));
  };

  const handleUpdate = (changes: Partial<LightConfig>) => {
    if (!selected_light_id) return;
    dispatch(updateLight({ id: selected_light_id, changes }));
  };

  return (
    <div
      data-testid="light-controller"
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        overflow: 'hidden',
      }}
    >
      {/* Surface type badge */}
      {material_result?.surface_type && (
        <div style={{ padding: '8px 12px 0' }}>
          <div
            data-testid="surface-type-badge"
            style={{
              display: 'inline-block',
              padding: '2px 8px',
              borderRadius: 4,
              fontSize: '0.7rem',
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid #3a3a3a',
              color: '#a0a0a0',
            }}
          >
            {material_result.surface_type}
          </div>
        </div>
      )}

      {/* Toolbar */}
      <div
        style={{
          display: 'flex',
          gap: 6,
          padding: '8px 12px',
          borderBottom: '1px solid #1a1a1a',
          flexShrink: 0,
        }}
      >
        <button
          data-testid="add-light-btn"
          onClick={handleAddLight}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            padding: '4px 8px',
            background: 'rgba(255,255,255,0.05)',
            border: '1px solid #2a2a2a',
            borderRadius: 4,
            color: '#a0a0a0',
            fontSize: '0.75rem',
            cursor: 'pointer',
            transition: 'all 150ms ease-in-out',
          }}
        >
          <Plus size={12} />
          Add Light
        </button>

        {selected_light_id && (
          <button
            data-testid="remove-light-btn"
            onClick={handleRemoveLight}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              padding: '4px 8px',
              background: 'rgba(248,113,113,0.08)',
              border: '1px solid rgba(248,113,113,0.2)',
              borderRadius: 4,
              color: '#f87171',
              fontSize: '0.75rem',
              cursor: 'pointer',
              transition: 'all 150ms ease-in-out',
            }}
          >
            <Trash2 size={12} />
            Remove
          </button>
        )}
      </div>

      {/* Empty state */}
      {lights.length === 0 && (
        <div
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <p style={{ color: '#555555', fontSize: '0.75rem', textAlign: 'center' }}>
            Controls will appear here
          </p>
        </div>
      )}

      {/* Light list */}
      {lights.length > 0 && (
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '8px 12px',
            display: 'flex',
            flexDirection: 'column',
            gap: 4,
          }}
        >
          {lights.map(light => (
            <button
              key={light.id}
              data-testid={`light-list-item-${light.id}`}
              onClick={() => dispatch(selectLight(light.id))}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '6px 8px',
                background:
                  light.id === selected_light_id
                    ? 'rgba(255,255,255,0.08)'
                    : 'rgba(255,255,255,0.02)',
                border:
                  light.id === selected_light_id ? '1px solid #3a3a3a' : '1px solid #1a1a1a',
                borderRadius: 4,
                color: '#a0a0a0',
                fontSize: '0.75rem',
                cursor: 'pointer',
                transition: 'all 150ms ease-in-out',
                textAlign: 'left',
              }}
            >
              <span
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  background: '#555',
                  flexShrink: 0,
                }}
              />
              <span style={{ flex: 1, color: '#f5f5f5', fontSize: '0.7rem' }}>
                {SHAPE_LABELS[light.shape]} ({light.type.toUpperCase()})
              </span>
            </button>
          ))}
        </div>
      )}

      {/* Selected light detail */}
      {selectedLight && (
        <div
          data-testid="selected-light-detail"
          style={{
            borderTop: '1px solid #1a1a1a',
            padding: '10px 12px',
            overflowY: 'auto',
            flexShrink: 0,
            maxHeight: '60%',
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
          }}
        >
          {/* Shape & Type */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
            <div>
              <p style={labelStyle}>Shape</p>
              <select
                data-testid="shape-select"
                value={selectedLight.shape}
                onChange={e =>
                  handleUpdate({ shape: e.target.value as LightConfig['shape'] })
                }
                style={inputStyle}
              >
                {SHAPE_OPTIONS.map(s => (
                  <option key={s} value={s}>
                    {SHAPE_LABELS[s]}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <p style={labelStyle}>Type</p>
              <select
                data-testid="type-select"
                value={selectedLight.type}
                onChange={e =>
                  handleUpdate({ type: e.target.value as LightConfig['type'] })
                }
                style={inputStyle}
              >
                {TYPE_OPTIONS.map(t => (
                  <option key={t} value={t}>
                    {TYPE_LABELS[t]}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Position */}
          <div>
            <p style={labelStyle}>Position (mm)</p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 4 }}>
              {(['x', 'y', 'z'] as const).map(axis => (
                <div key={axis}>
                  <p style={{ ...labelStyle, color: '#3a3a3a' }}>{axis.toUpperCase()}</p>
                  <input
                    data-testid={`pos-${axis}`}
                    type="number"
                    value={selectedLight.position[axis]}
                    onChange={e =>
                      handleUpdate({
                        position: {
                          ...selectedLight.position,
                          [axis]: parseFloat(e.target.value) || 0,
                        },
                      })
                    }
                    style={inputStyle}
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Angles */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
            <div>
              <p style={labelStyle}>Pitch (°)</p>
              <input
                data-testid="angle-pitch"
                type="number"
                value={selectedLight.pitch ?? 45}
                onChange={e => handleUpdate({ pitch: parseFloat(e.target.value) || 0 })}
                style={inputStyle}
              />
            </div>
            <div>
              <p style={labelStyle}>Yaw (°)</p>
              <input
                data-testid="angle-yaw"
                type="number"
                value={selectedLight.yaw ?? 0}
                onChange={e => handleUpdate({ yaw: parseFloat(e.target.value) || 0 })}
                style={inputStyle}
              />
            </div>
          </div>

          {/* LWD */}
          <div>
            <p style={labelStyle}>LWD (mm)</p>
            <input
              data-testid="lwd-input"
              type="number"
              value={selectedLight.lwd ?? 300}
              onChange={e => handleUpdate({ lwd: parseFloat(e.target.value) || 0 })}
              style={inputStyle}
            />
          </div>

          {/* Intensity */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <p style={labelStyle}>Intensity</p>
              <span style={{ color: '#a0a0a0', fontSize: '0.7rem' }}>
                {selectedLight.intensity}%
              </span>
            </div>
            <input
              data-testid="intensity-slider"
              type="range"
              min={0}
              max={100}
              value={selectedLight.intensity}
              onChange={e => handleUpdate({ intensity: parseInt(e.target.value, 10) })}
              style={{ width: '100%', accentColor: '#a0a0a0', transition: 'all 150ms ease-in-out' }}
            />
          </div>

          {/* Size */}
          {(selectedLight.shape === 'ring' ||
            selectedLight.shape === 'bar' ||
            selectedLight.shape === 'dome' ||
            selectedLight.shape === 'low_angle_ring') && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
              <div>
                <p style={labelStyle}>Width (mm)</p>
                <input
                  data-testid="size-width"
                  type="number"
                  value={selectedLight.size?.width ?? 50}
                  onChange={e =>
                    handleUpdate({
                      size: { width: parseFloat(e.target.value) || 0, height: selectedLight.size?.height ?? 50 },
                    })
                  }
                  style={inputStyle}
                />
              </div>
              <div>
                <p style={labelStyle}>Height (mm)</p>
                <input
                  data-testid="size-height"
                  type="number"
                  value={selectedLight.size?.height ?? 50}
                  onChange={e =>
                    handleUpdate({
                      size: { width: selectedLight.size?.width ?? 50, height: parseFloat(e.target.value) || 0 },
                    })
                  }
                  style={inputStyle}
                />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
