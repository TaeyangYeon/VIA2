import { useEffect, useState } from 'react';
import { Provider } from 'react-redux';
import { store } from './store';
import Layout from './components/Layout';
import LightTestWindow from './components/light_test/LightTestWindow';
import EngineSetupGuide from './components/EngineSetupGuide';

type ElectronAPI = {
  openLightTest?: () => void;
  onEngineStatus?: (cb: (data: { reachable: boolean; mode: 'local' | 'remote'; url: string }) => void) => void;
  removeEngineStatusListener?: () => void;
  retryEngineCheck?: () => void;
};

function getElectronAPI(): ElectronAPI | undefined {
  return (window as unknown as { electronAPI?: ElectronAPI }).electronAPI;
}

function App() {
  const isLightTest = window.location.hash === '#/light-test';
  const [showEngineGuide, setShowEngineGuide] = useState(false);
  const [engineMode, setEngineMode] = useState<'local' | 'remote'>('local');
  const [engineUrl, setEngineUrl] = useState<string>('');

  useEffect(() => {
    const api = getElectronAPI();
    if (!api?.onEngineStatus) return;

    api.onEngineStatus((data) => {
      setEngineMode(data.mode);
      setEngineUrl(data.url);
      if (!data.reachable) {
        setShowEngineGuide(true);
      } else {
        setShowEngineGuide(false);
      }
    });

    return () => {
      api.removeEngineStatusListener?.();
    };
  }, []);

  const handleRetry = () => {
    getElectronAPI()?.retryEngineCheck?.();
  };

  return (
    <div data-testid="app-root">
      <Provider store={store}>
        {isLightTest ? <LightTestWindow /> : <Layout />}
        <EngineSetupGuide
          isOpen={showEngineGuide}
          engineMode={engineMode}
          remoteUrl={engineUrl}
          onClose={() => setShowEngineGuide(false)}
          onRetry={handleRetry}
        />
      </Provider>
    </div>
  );
}

export default App;
