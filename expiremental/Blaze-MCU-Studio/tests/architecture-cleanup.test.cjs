'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { registerEndpoints } = require('../electron/ipc-routes.cjs');
const main = fs.readFileSync(path.join(__dirname, '../electron/main.cjs'), 'utf8');
const smoke = fs.readFileSync(path.join(__dirname, '../electron/gui-smoke.cjs'), 'utf8');

test('desktop bootstrap contains no embedded GUI smoke or IPC handler registry', () => {
  assert.match(main, /registerEndpoints\(/);
  assert.match(main, /installGuiSmoke\(/);
  assert.doesNotMatch(main, /executeJavaScript\(|ipcMain\.handle\(|register\('project:list'/);
  assert.match(smoke, /sessionRestoreUI/);
  assert.match(smoke, /typedDataDragGUI/);
});

test('all expected preload IPC channels stay registered exactly once', () => {
  const channels = new Map();
  const owned = { id: 1 };
  const ipcMain = {handle(name, handler) {
    assert(!channels.has(name), 'Duplicate IPC channel: ' + name);
    channels.set(name, handler);
  }};
  const store = { list: () => [{id:'mock'}] };
  registerEndpoints({
    ipcMain, dialog: {}, win: {webContents: owned}, store,
    workspaceCatalog: {}, desktopSession: {}, cli: '/missing-cli',
    simulations: {}
  });
  const required = [
    'project:list','project:create','project:open','project:save',
    'project:export','project:generate','cli:boards','cli:compile',
    'board:profile','pins:plan','session:load','session:save',
    'workspace:list','workspace:create','library:scan',
    'sim:create','sim:analog','resources:analyze'
  ];
  for (const name of required) assert(channels.has(name), 'Missing channel: ' + name);
  assert.equal(channels.size, 39);
  assert.deepEqual(channels.get('project:list')({sender:owned}), [{id:'mock'}]);
  assert.throws(
    () => channels.get('project:list')({sender:{id:1}}),
    /Untrusted IPC sender/
  );
});
