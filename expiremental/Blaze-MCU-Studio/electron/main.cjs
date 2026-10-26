'use strict';
const {app,BrowserWindow,ipcMain,dialog,session}=require('electron');const path=require('node:path');
const {WorkspaceStore}=require('../core/storage.cjs');const arduino=require('../core/arduino.cjs');const {analyzeGraph,generateSketch}=require('../core/project.cjs');
let win,store,cli;
function checkedSender(event){if(!win || event.sender!==win.webContents)throw Error('Untrusted IPC sender');}
function register(channel,fn){ipcMain.handle(channel,(event,...args)=>{checkedSender(event);return fn(...args);});}
app.whenReady().then(()=>{
 store=new WorkspaceStore(path.join(app.getPath('userData'),'projects'));cli=arduino.findCli(process.resourcesPath);
 session.defaultSession.setPermissionRequestHandler((_w,_p,cb)=>cb(false));
 win=new BrowserWindow({width:1350,height:810,minWidth:900,minHeight:620,show:false,backgroundColor:'#121721',webPreferences:{nodeIntegration:false,contextIsolation:true,sandbox:true,preload:path.join(__dirname,'preload.cjs'),webSecurity:true}});
 win.webContents.setWindowOpenHandler(()=>({action:'deny'}));win.webContents.on('will-navigate',e=>e.preventDefault());
 win.loadFile(path.join(__dirname,'../renderer/index.html'));win.once('ready-to-show',()=>win.show());
 register('project:list',()=>store.list());register('project:create',(name,fqbn)=>store.create(name,fqbn));register('project:open',id=>store.open(id));register('project:save',p=>store.save(p));
 register('project:validate',p=>{const d=analyzeGraph(p);return {...d,ordered:d.ordered.map(n=>n.id)};});register('project:generate',p=>generateSketch(p));
 register('project:export',async p=>{const result=await dialog.showOpenDialog(win,{properties:['openDirectory','createDirectory'],title:'Export Arduino-compatible sketch'});return result.canceled?{canceled:true}:store.export(p,result.filePaths[0]);});
 register('cli:status',()=>arduino.run(cli,['version']));register('cli:boards',()=>arduino.boardList(cli));register('cli:install',id=>arduino.platformInstall(cli,id));register('cli:compile',p=>arduino.compile(cli,p));
});app.on('window-all-closed',()=>{if(process.platform!=='darwin')app.quit()});
