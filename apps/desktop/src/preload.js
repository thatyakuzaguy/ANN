const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("annDesktop", {
  selectModelFile: () => ipcRenderer.invoke("ann:select-model-file")
});
