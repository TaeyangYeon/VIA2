import { Provider } from 'react-redux';
import { store } from './store';
import Layout from './components/Layout';
import LightTestWindow from './components/light_test/LightTestWindow';

function App() {
  const isLightTest = window.location.hash === '#/light-test';

  return (
    <div data-testid="app-root">
      <Provider store={store}>
        {isLightTest ? <LightTestWindow /> : <Layout />}
      </Provider>
    </div>
  );
}

export default App;
