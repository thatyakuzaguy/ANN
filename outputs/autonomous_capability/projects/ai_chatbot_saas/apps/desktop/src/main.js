const { app, BrowserWindow, shell } = require("electron");
const { spawn } = require("child_process");
const http = require("http");
const path = require("path");

const ROOT = path.resolve(__dirname, "..", "..", "..");
const WEB_URL = process.env.WEB_URL || "http://localhost:3000";

let childProcess;

function requestOk(url) {
  return new Promise((resolve) => {
    const req = http.get(url, { timeout: 1500 }, (res) => {
      res.resume();
      resolve(res.statusCode >= 200 && res.statusCode < 500);
    });
    req.on("timeout", () => {
      req.destroy();
      resolve(false);
    });
    req.on("error", () => resolve(false));
  });
}

async function waitForWeb() {
  for (let i = 0; i < 60; i += 1) {
    if (await requestOk(WEB_URL)) return true;
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  return false;
}

function startStack() {
  childProcess = spawn("powershell.exe", ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "scripts/start.ps1"], {
    cwd: ROOT,
    windowsHide: true,
    stdio: "ignore"
  });
}

async function createWindow() {
  const win = new BrowserWindow({
    width: 1320,
    height: 860,
    minWidth: 1000,
    minHeight: 700,
    title: "AI Chatbot SaaS",
    backgroundColor: "#0d1117",
    webPreferences: { contextIsolation: true, nodeIntegration: false, sandbox: true }
  });
  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });
  startStack();
  if (await waitForWeb()) {
    await win.loadURL(WEB_URL);
  } else {
    await win.loadURL("data:text/html,<h1>AI Chatbot SaaS</h1><p>Could not start local services.</p>");
  }
}

app.whenReady().then(createWindow);
app.on("window-all-closed", () => app.quit());
