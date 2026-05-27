const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  openLightTest: () => ipcRenderer.send('open-light-test'),
});
