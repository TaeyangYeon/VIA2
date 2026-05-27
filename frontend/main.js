const { app, BrowserWindow, ipcMain, Menu } = require('electron');
const path = require('path');

const isDev = process.env.ELECTRON_DEV === 'true' || !app.isPackaged;

let lightTestWindow = null;

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 960,
    minHeight: 600,
    backgroundColor: '#0a0a0a',
    titleBarStyle: 'hiddenInset',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    show: false,
  });

  if (isDev) {
    win.loadURL('http://localhost:5173');
    win.webContents.openDevTools();
  } else {
    win.loadFile(path.join(__dirname, 'dist', 'index.html'));
  }

  win.once('ready-to-show', () => {
    win.show();
  });
}

function createLightTestWindow() {
  if (lightTestWindow) {
    lightTestWindow.focus();
    return;
  }

  lightTestWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    backgroundColor: '#0a0a0a',
    titleBarStyle: 'hiddenInset',
    title: 'VIA2 — Light Test',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    show: false,
  });

  if (isDev) {
    lightTestWindow.loadURL('http://localhost:5173/#/light-test');
  } else {
    lightTestWindow.loadFile(path.join(__dirname, 'dist', 'index.html'), {
      hash: '/light-test',
    });
  }

  lightTestWindow.once('ready-to-show', () => {
    lightTestWindow.show();
  });

  lightTestWindow.on('closed', () => {
    lightTestWindow = null;
  });
}

ipcMain.on('open-light-test', () => {
  createLightTestWindow();
});

function buildMenu() {
  const template = [
    {
      label: 'VIA2',
      submenu: [
        { role: 'about' },
        { type: 'separator' },
        { role: 'quit' },
      ],
    },
    {
      label: 'Tools',
      submenu: [
        {
          label: 'Light Test',
          accelerator: 'CmdOrCtrl+Shift+L',
          click: () => createLightTestWindow(),
        },
      ],
    },
    {
      label: 'Window',
      submenu: [
        { role: 'minimize' },
        { role: 'zoom' },
        { type: 'separator' },
        { role: 'front' },
      ],
    },
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

app.whenReady().then(() => {
  buildMenu();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
