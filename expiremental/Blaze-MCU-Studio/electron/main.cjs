'use strict';
const { app, BrowserWindow, ipcMain, dialog, session } = require('electron');
const path = require('node:path');

const { WorkspaceStore } = require('../core/storage.cjs');
const { WorkspaceCatalog } = require('../core/workspaces.cjs');
const { DesktopSession } = require('../core/desktop-session.cjs');
const arduino = require('../core/arduino.cjs');
const { SimulationController } = require('../core/simulator.cjs');
const { registerEndpoints } = require('./ipc-routes.cjs');
const { installGuiSmoke } = require('./gui-smoke.cjs');

app.whenReady().then(() => {
  const store = new WorkspaceStore(path.join(app.getPath('userData'), 'projects'));
  const workspaceCatalog = new WorkspaceCatalog(store);
  const desktopSession = new DesktopSession(store, workspaceCatalog);
  const cli = arduino.findCli(process.resourcesPath);
  const simulations = new SimulationController();

  session.defaultSession.setPermissionRequestHandler((_webContents, _permission, respond) => respond(false));

  const win = new BrowserWindow({
    width: 1350, height: 810, minWidth: 900, minHeight: 620,
    show: false, backgroundColor: '#121721',
    webPreferences: {
      nodeIntegration: false, contextIsolation: true, sandbox: true,
      preload: path.join(__dirname, 'preload.cjs'), webSecurity: true
    }
  });
  win.webContents.setWindowOpenHandler(() => ({action: 'deny'}));
  win.webContents.on('will-navigate', event => event.preventDefault());

  registerEndpoints({ ipcMain, dialog, win, store, workspaceCatalog, desktopSession, cli, simulations });
  installGuiSmoke(win, app);
  win.loadFile(path.join(__dirname, '../renderer/index.html'));
  win.once('ready-to-show', () => win.show());
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
