import { colors } from './styles/design-tokens';

function App() {
  return (
    <div
      data-testid="app-root"
      style={{ backgroundColor: colors.background.top, minHeight: '100vh' }}
    >
      <main
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          gap: '8px',
        }}
      >
        <h1
          style={{
            color: colors.text.primary,
            fontFamily: 'Inter, system-ui, sans-serif',
            fontSize: '2rem',
            fontWeight: 700,
            letterSpacing: '-0.02em',
            margin: 0,
          }}
        >
          VIA2
        </h1>
        <p
          style={{
            color: colors.text.secondary,
            fontFamily: 'Inter, system-ui, sans-serif',
            fontSize: '1rem',
            fontWeight: 400,
            margin: 0,
          }}
        >
          Vision Intelligence Agent
        </p>
      </main>
    </div>
  );
}

export default App;
