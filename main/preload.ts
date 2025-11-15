// Preload script for Electron main process
// Expose API to renderer if needed

const { contextBridge } = require('electron');

// Example: expose a secure API

contextBridge.exposeInMainWorld('electronAPI', {
  // Add methods here if needed
});

// You can add more preload variables or APIs as needed
