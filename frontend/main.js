const { app, BrowserWindow, ipcMain, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');
const https = require('https');
const fs = require('fs');
const os = require('os');

const isDev = process.env.ELECTRON_DEV === 'true' || !app.isPackaged;

let lightTestWindow = null;
let backendProcess = null;
let mainWindow = null;

function startBackend() {
  const projectRoot = path.join(__dirname, '..');
  backendProcess = spawn(
    'python',
    ['-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', '8000'],
    {
      cwd: projectRoot,
      env: { ...process.env },
    }
  );

  backendProcess.stdout.on('data', (data) => {
    console.log(`[backend] ${data.toString().trim()}`);
  });

  backendProcess.stderr.on('data', (data) => {
    console.log(`[backend] ${data.toString().trim()}`);
  });

  backendProcess.on('error', (err) => {
    console.error('[backend] spawn error:', err);
  });

  backendProcess.on('exit', (code) => {
    console.log(`[backend] process exited with code ${code}`);
    backendProcess = null;
  });
}

function checkEngineHealth(win) {
  let config = { mode: 'local', url: 'http://localhost:11434' };
  const configPath = path.join(os.homedir(), '.via2', 'engine_config.json');
  try {
    if (fs.existsSync(configPath)) {
      const raw = fs.readFileSync(configPath, 'utf-8');
      config = { ...config, ...JSON.parse(raw) };
    }
  } catch (e) {
    console.warn('[engine] Failed to read engine config:', e.message);
  }

  const { mode, url } = config;
  const endpoint = mode === 'local' ? `${url}/api/tags` : `${url}/health`;
  const lib = endpoint.startsWith('https') ? https : http;

  let parsedUrl;
  try {
    parsedUrl = new URL(endpoint);
  } catch (e) {
    win.webContents.send('engine-status', { reachable: false, mode, url });
    return;
  }

  const options = {
    hostname: parsedUrl.hostname,
    port: parsedUrl.port || (parsedUrl.protocol === 'https:' ? 443 : 80),
    path: parsedUrl.pathname,
    method: 'GET',
    timeout: 3000,
  };

  const req = lib.request(options, () => {
    win.webContents.send('engine-status', { reachable: true, mode, url });
  });

  req.on('timeout', () => {
    req.destroy();
    win.webContents.send('engine-status', { reachable: false, mode, url });
  });

  req.on('error', () => {
    win.webContents.send('engine-status', { reachable: false, mode, url });
  });

  req.end();
}

function createWindow() {
  mainWindow = new BrowserWindow({
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
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, 'dist', 'index.html'));
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    checkEngineHealth(mainWindow);
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

ipcMain.on('retry-engine-check', () => {
  if (mainWindow) {
    checkEngineHealth(mainWindow);
  }
});

app.on('before-quit', () => {
  if (backendProcess) {
    backendProcess.kill('SIGTERM');
    const proc = backendProcess;
    setTimeout(() => {
      if (proc) {
        proc.kill('SIGKILL');
      }
    }, 2000);
  }
});

app.whenReady().then(() => {
  buildMenu();
  startBackend();
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
