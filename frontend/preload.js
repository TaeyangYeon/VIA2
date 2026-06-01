const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  openLightTest: () => ipcRenderer.send('open-light-test'),
  onEngineStatus: (callback) => ipcRenderer.on('engine-status', (_event, data) => callback(data)),
  removeEngineStatusListener: () => ipcRenderer.removeAllListeners('engine-status'),
  retryEngineCheck: () => ipcRenderer.send('retry-engine-check'),
});
