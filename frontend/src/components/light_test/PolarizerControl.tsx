import { useAppDispatch, useAppSelector } from '../../store';
import { updateLight, setLensPolarizer } from '../../store/slices/lightTestSlice';

const POLARIZER_SHAPES = new Set(['ring', 'bar', 'coaxial', 'dome', 'low_angle_ring']);

const labelStyle: React.CSSProperties = {
  color: '#555555',
  fontSize: '0.65rem',
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
  marginBottom: 2,
};

export default function PolarizerControl() {
  const dispatch = useAppDispatch();
  const selectedId = useAppSelector(s => s.light_test.selected_light_id);
  const lights = useAppSelector(s => s.light_test.lights);
  const lens_polarizer_angle = useAppSelector(s => s.light_test.lens_polarizer_angle);

  const selectedLight = lights.find(l => l.id === selectedId) ?? null;

  const handlePolarizerEnabled = (checked: boolean) => {
    if (!selectedId) return;
    dispatch(updateLight({ id: selectedId, changes: { polarizer_enabled: checked } }));
  };

  const handleSpotAngle = (value: number) => {
    if (!selectedId) return;
    dispatch(updateLight({ id: selectedId, changes: { polarizer_angle: value } }));
  };

  const isSpot = selectedLight?.shape === 'spot';
  const supportsLightPolarizer =
    selectedLight != null && POLARIZER_SHAPES.has(selectedLight.shape);

  return (
    <div
      data-testid="polarizer-control"
      style={{
        padding: '8px 12px',
        borderTop: '1px solid #1a1a1a',
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
      }}
    >
      {/* Light-side polarizer section */}
      {selectedLight && (
        <div>
          <p style={{ ...labelStyle, marginBottom: 6 }}>Light Polarizer</p>

          {isSpot ? (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <p style={labelStyle}>편광 각도 (°)</p>
                <span
                  data-testid="lens-polarizer-value"
                  style={{ color: '#a0a0a0', fontSize: '0.7rem' }}
                >
                  {selectedLight.polarizer_angle ?? 0}°
                </span>
              </div>
              <input
                data-testid="light-polarizer-spot-dial"
                type="range"
                min={0}
                max={180}
                value={selectedLight.polarizer_angle ?? 0}
                onChange={e => handleSpotAngle(parseInt(e.target.value, 10))}
                style={{ width: '100%', accentColor: '#a0a0a0' }}
              />
            </div>
          ) : (
            <label
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                cursor: supportsLightPolarizer ? 'pointer' : 'default',
                opacity: supportsLightPolarizer ? 1 : 0.4,
              }}
            >
              <input
                data-testid="light-polarizer-checkbox"
                type="checkbox"
                checked={selectedLight.polarizer_enabled ?? false}
                disabled={!supportsLightPolarizer}
                onChange={e => handlePolarizerEnabled(e.target.checked)}
                style={{ accentColor: '#a0a0a0' }}
              />
              <span style={{ color: '#a0a0a0', fontSize: '0.75rem' }}>편광 필름 적용</span>
            </label>
          )}
        </div>
      )}

      {/* Lens-side polarizer section */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <p style={labelStyle}>렌즈 편광 각도</p>
          <span
            data-testid="lens-polarizer-value"
            style={{ color: '#a0a0a0', fontSize: '0.7rem' }}
          >
            {lens_polarizer_angle}°
          </span>
        </div>
        <input
          data-testid="lens-polarizer-slider"
          type="range"
          min={0}
          max={180}
          value={lens_polarizer_angle}
          onChange={e => dispatch(setLensPolarizer(parseInt(e.target.value, 10)))}
          style={{ width: '100%', accentColor: '#a0a0a0' }}
        />
      </div>
    </div>
  );
}
