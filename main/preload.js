// Preload script for Electron main process

const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Add methods here if needed
});
