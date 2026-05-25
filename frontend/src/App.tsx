import { Provider } from 'react-redux';
import { store } from './store';
import Layout from './components/Layout';

function App() {
  return (
    <div data-testid="app-root">
      <Provider store={store}>
        <Layout />
      </Provider>
    </div>
  );
}

export default App;
