'use strict';

// Electron IPC boundary. Callers cannot bypass the currently owned BrowserWindow.
const arduino = require('../core/arduino.cjs');
const { generateSketch } = require('../core/project.cjs');
const balie = require('../core/balie.cjs');
const board = require('../core/board.cjs');
const flow = require('../core/flowchart.cjs');
const resources = require('../core/resources.cjs');
const peripherals = require('../core/peripherals.cjs');
const variables = require('../core/variables.cjs');

function registerEndpoints({ ipcMain, dialog, win, store, workspaceCatalog, desktopSession, cli, simulations }) {
  if (!ipcMain || !win?.webContents) throw new Error('Missing Electron IPC or trusted window');
  const register = (channel, handler) => {
    ipcMain.handle(channel, (event, ...args) => {
      if (event.sender !== win.webContents) throw new Error('Untrusted IPC sender');
      return handler(...args);
    });
  };

 register('session:load',()=>desktopSession.load());register('session:save',state=>desktopSession.save(state));
 register('workspace:list',()=>workspaceCatalog.list());register('workspace:create',name=>workspaceCatalog.create(name));register('workspace:rename',(id,name)=>workspaceCatalog.rename(id,name));register('workspace:add',(id,pid)=>workspaceCatalog.add(id,pid));register('workspace:remove',(id,pid)=>workspaceCatalog.remove(id,pid));register('workspace:delete',id=>workspaceCatalog.delete(id));register('project:list',()=>store.list());register('project:create',(name,fqbn,template)=>store.create(name,fqbn,template));register('project:open',id=>store.open(id));register('project:save',p=>store.save(p));
 register('project:validate',p=>{const d=generateSketch(p).diagnostics;return {...d,ordered:(d.ordered||[]).map(n=>n.id)};});register('project:generate',p=>generateSketch(p));
 register('project:rename',(id,name)=>store.rename(id,name));register('project:duplicate',id=>store.duplicate(id));register('project:trash',id=>store.trash(id));register('project:recoveryList',()=>store.recoveryList());register('project:recover',id=>store.recover(id));
 register('board:migration',(p,target)=>board.analyzeBoardChange(p,target));register('board:profile',fqbn=>board.profile(fqbn));
 register('flow:trace',(p,input)=>flow.traceFlowchart(p.flowchart||flow.sampleFlowchart(),input,1000));
 register('library:scan',p=>balie.scanInstalled({architecture:p.fqbn.split(':')[1]}));
 register('library:inspect',async p=>{const result=await dialog.showOpenDialog(win,{properties:['openDirectory'],title:'Inspect installed Arduino library directory (read-only)'});if(result.canceled)return {canceled:true};return balie.inspectLibrary(result.filePaths[0],p.fqbn.split(':')[1]);});
 register('sim:create',(p,inputs)=>simulations.create(p,inputs));
 register('sim:step',id=>simulations.step(id));
 register('sim:run',(id,budget)=>simulations.run(id,{maxSteps:budget}));
 register('sim:inputs',(id,inputs)=>simulations.inputs(id,inputs));
 register('sim:analog',(id,inputs)=>simulations.analog(id,inputs));
 register('project:validateVariables',list=>variables.validate(list).errors.length?{errors:variables.validate(list).errors}:{errors:[]});
 register('sim:breakpoints',(id,ids)=>simulations.breakpoints(id,ids));
 register('sim:dispose',id=>simulations.dispose(id));
 register('resources:analyze',(p,compilation,config)=>resources.analyzeResources(p,compilation,config));
 register('pins:plan',p=>peripheralPlanner.plan(p));
 register('project:export',async p=>{const result=await dialog.showOpenDialog(win,{properties:['openDirectory','createDirectory'],title:'Export Arduino-compatible sketch'});return result.canceled?{canceled:true}:store.export(p,result.filePaths[0]);});
 register('cli:status',()=>arduino.run(cli,['version']));register('cli:boards',()=>arduino.boardList(cli));register('cli:install',id=>arduino.platformInstall(cli,id));register('cli:compile',p=>arduino.compile(cli,p));

}
module.exports = { registerEndpoints };
