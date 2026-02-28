const { app, BrowserWindow } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const http = require("http");

const PORT = 8000;
const HEALTH_URL = `http://127.0.0.1:${PORT}/health`;
const APP_URL = `http://127.0.0.1:${PORT}`;

// When packaged: .app/Contents/MacOS/Chat Agent -> project root = parent of .app
// When dev (electron .): __dirname = desktop/, project root = parent
function getProjectRoot() {
  if (app.isPackaged) {
    return path.resolve(path.dirname(process.execPath), "..", "..", "..");
  }
  return path.resolve(__dirname, "..");
}

let backendProcess = null;

function startBackend(projectRoot) {
  const backendDir = path.join(projectRoot, "backend");
  const uvicorn = path.join(backendDir, "venv", "bin", "uvicorn");
  const env = { ...process.env, CHAT_AGENT_ROOT: projectRoot };
  backendProcess = spawn(uvicorn, ["app.main:app", "--host", "127.0.0.1", "--port", String(PORT)], {
    cwd: backendDir,
    env,
    stdio: "pipe",
  });
  backendProcess.on("error", (err) => {
    console.error("Backend failed to start:", err);
  });
  backendProcess.stderr?.on("data", (d) => process.stderr.write(d));
  return backendProcess;
}

function waitForServer(maxWaitMs = 30000, intervalMs = 300) {
  return new Promise((resolve, reject) => {
    const deadline = Date.now() + maxWaitMs;
    function tryOnce() {
      const req = http.get(HEALTH_URL, { timeout: 2000 }, (res) => {
        if (res.statusCode === 200) {
          resolve();
          return;
        }
        scheduleNext();
      });
      req.on("error", () => scheduleNext());
      req.on("timeout", () => {
        req.destroy();
        scheduleNext();
      });
    }
    function scheduleNext() {
      if (Date.now() > deadline) {
        reject(new Error("Server did not start in time"));
        return;
      }
      setTimeout(tryOnce, intervalMs);
    }
    tryOnce();
  });
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1000,
    height: 700,
    minWidth: 600,
    minHeight: 400,
    title: "Chat Agent",
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  });
  win.once("ready-to-show", () => win.show());
  win.loadURL(APP_URL);
  win.on("closed", () => {
    if (backendProcess) {
      backendProcess.kill();
      backendProcess = null;
    }
  });
}

app.whenReady().then(async () => {
  const projectRoot = getProjectRoot();
  const backendDir = path.join(projectRoot, "backend");
  const uvicornPath = path.join(backendDir, "venv", "bin", "uvicorn");
  const { dialog } = require("electron");

  if (!require("fs").existsSync(uvicornPath)) {
    dialog.showErrorBox(
      "Chat Agent",
      "Backend not found. Run ./install.sh in the project folder first.\n\nProject: " + projectRoot
    );
    app.quit();
    return;
  }

  // Show a loading window while server starts
  const loading = new BrowserWindow({
    width: 400,
    height: 120,
    title: "Chat Agent",
    minimizable: false,
    webPreferences: { nodeIntegration: false },
  });
  loading.setMenuBarVisibility(false);
  loading.loadURL(
    "data:text/html," +
      encodeURIComponent(
        "<!DOCTYPE html><html><head><style>body{font-family:system-ui;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;background:#1a1a1a;color:#eee;}</style></head><body><p>Starting server…</p></body></html>"
      )
  );

  startBackend(projectRoot);
  try {
    await waitForServer();
  } catch (e) {
    loading.close();
    dialog.showErrorBox(
      "Chat Agent",
      "Server failed to start. Check that Ollama is running and port 8000 is free."
    );
    app.quit();
    return;
  }
  loading.close();
  createWindow();
});

app.on("window-all-closed", () => {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
  app.quit();
});
