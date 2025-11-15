import { app, BrowserWindow } from 'electron';
import * as path from 'path';
import { spawn } from 'child_process';

const createWindow = () => {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, '../main/preload.js'),
    },
  });

  mainWindow.loadURL('http://localhost:3000');
};

let backendProcess: any;

app.whenReady().then(() => {
  // Spawn the backend
  backendProcess = spawn('uvicorn', ['app.main:app', '--host', '127.0.0.1', '--port', '8000'], {
    cwd: path.join(__dirname, '../backend'),
    stdio: 'inherit'
  });

  backendProcess.on('error', (err: any) => {
    console.error('Failed to start backend:', err);
  });

  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('before-quit', () => {
  if (backendProcess) {
    backendProcess.kill();
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
