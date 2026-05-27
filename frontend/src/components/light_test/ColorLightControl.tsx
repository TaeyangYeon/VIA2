import { useAppDispatch, useAppSelector } from '../../store';
import { updateLight } from '../../store/slices/lightTestSlice';

const labelStyle: React.CSSProperties = {
  color: '#555555',
  fontSize: '0.65rem',
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
  marginBottom: 2,
};

const sliderStyle: React.CSSProperties = {
  width: '100%',
  accentColor: '#a0a0a0',
};

function toHex(r: number, g: number, b: number): string {
  return (
    '#' +
    [r, g, b]
      .map(v => Math.round(Math.max(0, Math.min(255, v))).toString(16).padStart(2, '0'))
      .join('')
  );
}

export default function ColorLightControl() {
  const dispatch = useAppDispatch();
  const selectedId = useAppSelector(s => s.light_test.selected_light_id);
  const lights = useAppSelector(s => s.light_test.lights);
  const isGrayscale = useAppSelector(s => s.light_test.is_grayscale);

  const selectedLight = lights.find(l => l.id === selectedId) ?? null;

  if (!selectedLight) return null;

  const color = selectedLight.color ?? { r: 255, g: 255, b: 255 };

  const handleChange = (channel: 'r' | 'g' | 'b', value: number) => {
    if (!selectedId) return;
    dispatch(
      updateLight({
        id: selectedId,
        changes: { color: { ...color, [channel]: value } },
      }),
    );
  };

  return (
    <div
      data-testid="color-light-control"
      style={{
        padding: '8px 12px',
        borderTop: '1px solid #1a1a1a',
        display: 'flex',
        flexDirection: 'column',
        gap: 6,
      }}
    >
      <p style={{ ...labelStyle, marginBottom: 4 }}>Color</p>

      {isGrayscale && (
        <p
          data-testid="color-disabled-message"
          style={{ color: '#555555', fontSize: '0.7rem' }}
        >
          컬러 기능은 컬러 이미지에서만 사용 가능합니다
        </p>
      )}

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <div
          data-testid="color-preview-swatch"
          style={{
            width: 24,
            height: 24,
            borderRadius: 4,
            border: '1px solid #3a3a3a',
            background: toHex(color.r, color.g, color.b),
            flexShrink: 0,
            opacity: isGrayscale ? 0.3 : 1,
          }}
        />
        <span style={{ color: '#707070', fontSize: '0.7rem' }}>
          {toHex(color.r, color.g, color.b).toUpperCase()}
        </span>
      </div>

      {(['r', 'g', 'b'] as const).map(ch => (
        <div key={ch}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <p style={labelStyle}>{ch.toUpperCase()}</p>
            <span style={{ color: '#a0a0a0', fontSize: '0.7rem' }}>{color[ch]}</span>
          </div>
          <input
            data-testid={`color-${ch}-slider`}
            type="range"
            min={0}
            max={255}
            value={color[ch]}
            disabled={isGrayscale}
            onChange={e => handleChange(ch, parseInt(e.target.value, 10))}
            style={{ ...sliderStyle, opacity: isGrayscale ? 0.3 : 1 }}
          />
        </div>
      ))}
    </div>
  );
}
