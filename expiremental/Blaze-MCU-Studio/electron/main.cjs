'use strict';
const {app,BrowserWindow,ipcMain,dialog,session}=require('electron');const path=require('node:path');
const {WorkspaceStore}=require('../core/storage.cjs');const arduino=require('../core/arduino.cjs');const {analyzeGraph,generateSketch}=require('../core/project.cjs');const balie=require('../core/balie.cjs');const board=require('../core/board.cjs');const flow=require('../core/flowchart.cjs');const {SimulationController}=require('../core/simulator.cjs');const resources=require('../core/resources.cjs');const peripheralPlanner=require('../core/peripherals.cjs');
let win,store,cli;const simulations=new SimulationController();
function checkedSender(event){if(!win || event.sender!==win.webContents)throw Error('Untrusted IPC sender');}
function register(channel,fn){ipcMain.handle(channel,(event,...args)=>{checkedSender(event);return fn(...args);});}
app.whenReady().then(()=>{
 store=new WorkspaceStore(path.join(app.getPath('userData'),'projects'));cli=arduino.findCli(process.resourcesPath);
 session.defaultSession.setPermissionRequestHandler((_w,_p,cb)=>cb(false));
 win=new BrowserWindow({width:1350,height:810,minWidth:900,minHeight:620,show:false,backgroundColor:'#121721',webPreferences:{nodeIntegration:false,contextIsolation:true,sandbox:true,preload:path.join(__dirname,'preload.cjs'),webSecurity:true}});
 win.webContents.setWindowOpenHandler(()=>({action:'deny'}));win.webContents.on('will-navigate',e=>e.preventDefault());
 win.loadFile(path.join(__dirname,'../renderer/index.html'));win.once('ready-to-show',()=>win.show());
 // CI-only end-to-end packaged GUI smoke. No production code path writes this file.
 if(process.env.BLAZE_MCU_SMOKE_FILE){
  const fs=require('node:fs');
  win.webContents.once('did-finish-load',async()=>{
   let report;
   try{
    report=await win.webContents.executeJavaScript(`(async()=>{
      const required=['projectList','graphCanvas','flowchartView','librariesView','simulateView','resourcesView','resourceOutput','simSummary'];
      const missing=required.filter(id=>!document.getElementById(id));
      const api=window.blaze;
      if(missing.length)throw Error('Missing renderer elements '+missing.join(','));
      if(!api?.createProject||!api?.simCreate||!api?.resourceAnalyze)throw Error('IPC preload API unavailable');
      const created=await api.createProject('CISmoke','arduino:avr:uno');
      const reopened=await api.openProject(created.id);
      const generated=await api.generate(reopened);
      if(!generated.source?.includes('digitalWrite(13, HIGH)'))throw Error('Generator not wired through preload');
      const sim=await api.simCreate(reopened,{});
      const trace=await api.simRun(sim.id,30);
      if(trace.outputs['13']!=='LOW'||trace.virtualTimeMs!==2000)throw Error('Simulator output mismatch');
      const resources=await api.resourceAnalyze(reopened,null,{intervalSeconds:10,bytesPerRecord:48,capacityBytes:1048576,retentionDays:7});
      if(resources.storage.recordsDay!==8640)throw Error('Resource advisor IPC mismatch');
      return {passed:true,renderer:true,ipc:true,generation:true,simulation:true,resources:true};
    })()`);
   }catch(e){report={passed:false,error:String(e?.stack||e)};}
   try{fs.writeFileSync(process.env.BLAZE_MCU_SMOKE_FILE,JSON.stringify(report,null,2));}catch(e){console.error('SMOKE REPORT WRITE FAILED',e);}
   setTimeout(()=>app.quit(),500);
  });
 }

 register('project:list',()=>store.list());register('project:create',(name,fqbn)=>store.create(name,fqbn));register('project:open',id=>store.open(id));register('project:save',p=>store.save(p));
 register('project:validate',p=>{const d=generateSketch(p).diagnostics;return {...d,ordered:(d.ordered||[]).map(n=>n.id)};});register('project:generate',p=>generateSketch(p));
 register('project:rename',(id,name)=>store.rename(id,name));register('project:duplicate',id=>store.duplicate(id));register('project:trash',id=>store.trash(id));register('project:recoveryList',()=>store.recoveryList());register('project:recover',id=>store.recover(id));
 register('board:migration',(p,target)=>board.analyzeBoardChange(p,target));
 register('flow:trace',(p,input)=>flow.traceFlowchart(p.flowchart||flow.sampleFlowchart(),input,1000));
 register('library:scan',p=>balie.scanInstalled({architecture:p.fqbn.split(':')[1]}));
 register('library:inspect',async p=>{const result=await dialog.showOpenDialog(win,{properties:['openDirectory'],title:'Inspect installed Arduino library directory (read-only)'});if(result.canceled)return {canceled:true};return balie.inspectLibrary(result.filePaths[0],p.fqbn.split(':')[1]);});
 register('sim:create',(p,inputs)=>simulations.create(p,inputs));
 register('sim:step',id=>simulations.step(id));
 register('sim:run',(id,budget)=>simulations.run(id,{maxSteps:budget}));
 register('sim:inputs',(id,inputs)=>simulations.inputs(id,inputs));
 register('sim:breakpoints',(id,ids)=>simulations.breakpoints(id,ids));
 register('sim:dispose',id=>simulations.dispose(id));
 register('resources:analyze',(p,compilation,config)=>resources.analyzeResources(p,compilation,config));
 register('pins:plan',p=>peripheralPlanner.plan(p));
 register('project:export',async p=>{const result=await dialog.showOpenDialog(win,{properties:['openDirectory','createDirectory'],title:'Export Arduino-compatible sketch'});return result.canceled?{canceled:true}:store.export(p,result.filePaths[0]);});
 register('cli:status',()=>arduino.run(cli,['version']));register('cli:boards',()=>arduino.boardList(cli));register('cli:install',id=>arduino.platformInstall(cli,id));register('cli:compile',p=>arduino.compile(cli,p));
});app.on('window-all-closed',()=>{if(process.platform!=='darwin')app.quit()});
