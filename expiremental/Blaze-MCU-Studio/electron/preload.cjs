'use strict';const {contextBridge,ipcRenderer}=require('electron');
const actions={listProjects:'project:list',createProject:'project:create',openProject:'project:open',saveProject:'project:save',validate:'project:validate',generate:'project:generate',exportSketch:'project:export',cliStatus:'cli:status',boards:'cli:boards',installCore:'cli:install',compile:'cli:compile'};
const api=Object.fromEntries(Object.entries(actions).map(([name,channel])=>[name,(...args)=>ipcRenderer.invoke(channel,...args)]));
contextBridge.exposeInMainWorld('blaze',Object.freeze(api));
