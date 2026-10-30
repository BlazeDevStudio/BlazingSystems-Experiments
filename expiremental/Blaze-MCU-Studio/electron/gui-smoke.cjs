'use strict';

// CI-only packaged renderer acceptance. Runs only with the explicit smoke output path.
// Keep this test harness outside the production startup and IPC registry.
function installGuiSmoke(win, app) {
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
      // Exercise the actual DOM handlers: first-project modal, board catalog, sidebar
      // drag/drop, node selection and inspector input (not merely backend IPC).
      const boardCatalog=await api.boards();
      if(!boardCatalog.boards.some(b=>b.fqbn==='esp8266:esp8266:generic'&&!b.installed))throw Error('Missing explicitly labeled optional ESP8266 target');
      document.getElementById('newProject').click();
      if(document.getElementById('newModal').classList.contains('hidden'))throw Error('New project dialog did not open');
      const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
      for(let i=0;i<70&&document.getElementById('newBoard').options.length<2;i++)await pause(100);
      if(document.getElementById('newBoard').options.length<2)throw Error('Board catalog failed to load into UI after modal opened');
      document.getElementById('boardSearch').value='ESP8266';
      document.getElementById('boardSearch').dispatchEvent(new Event('input',{bubbles:true}));
      if(!Array.from(document.getElementById('newBoard').options).some(o=>o.value==='esp8266:esp8266:generic'))throw Error('ESP8266 missing from displayed selectable starter targets');
      document.getElementById('boardSearch').value='';
      document.getElementById('boardSearch').dispatchEvent(new Event('input',{bubbles:true}));
      document.getElementById('newName').value='GuiSmoke';
      document.getElementById('newBoard').value='arduino:avr:uno';
      document.getElementById('newBoard').dispatchEvent(new Event('change',{bubbles:true}));
      document.getElementById('confirmNew').click();
      for(let i=0;i<80&&(document.getElementById('projectTitle').textContent!=='GuiSmoke'||document.getElementById('workspace').classList.contains('hidden'));i++)await pause(100);
      if(document.getElementById('projectTitle').textContent!=='GuiSmoke')throw Error('New project UI did not create/open project');
      const startCount=document.querySelectorAll('#nodeLayer [data-node]').length;
      const block=document.querySelector('[data-add="delay"]');
      const transfer=new DataTransfer();
      block.dispatchEvent(new DragEvent('dragstart',{bubbles:true,cancelable:true,dataTransfer:transfer}));
      const canvas=document.getElementById('graphCanvas');
      const bounds=canvas.getBoundingClientRect();
      canvas.dispatchEvent(new DragEvent('dragover',{bubbles:true,cancelable:true,dataTransfer:transfer,clientX:bounds.x+300,clientY:bounds.y+350}));
      canvas.dispatchEvent(new DragEvent('drop',{bubbles:true,cancelable:true,dataTransfer:transfer,clientX:bounds.x+300,clientY:bounds.y+350}));
      if(document.querySelectorAll('#nodeLayer [data-node]').length!==startCount+1)throw Error('Dragged palette block did not create a node');
      const added=[...document.querySelectorAll('#nodeLayer [data-node]')].find(n=>n.dataset.node.startsWith('delay_'));
      if(!added)throw Error('Dropped delay block not visible');
      added.querySelector('[data-select]').click();
      const prop=document.querySelector('#nodeInspector input[data-param="ms"]');
      if(!prop)throw Error('Node selection did not show inspector');
      prop.value='75';prop.dispatchEvent(new Event('input',{bubbles:true}));
      if(!document.querySelector('[data-node=\"'+added.dataset.node+'\"] .ndesc')?.textContent.includes('75'))throw Error('Inspector input did not update canvas');
      document.getElementById('save').click();
      await pause(350);
      const savedItems=await api.listProjects();
      const saved=savedItems.find(x=>x.name==='GuiSmoke');
      if(!saved)throw Error('UI created project not persisted');
      const savedProject=await api.openProject(saved.id);
      if(!savedProject.graph.nodes.some(n=>n.type==='delay'&&Number(n.params.ms)===75))throw Error('Inspector edit not persisted');
      document.querySelector('[data-tab="libraries"]').click();
      if(document.getElementById('curatedAdapter').classList.contains('hidden'))throw Error('Uno Wire adapter absent from Library palette');
      document.getElementById('addWireAdapter').click();
      const wireNode=[...document.querySelectorAll('#nodeLayer [data-node]')].find(n=>n.dataset.node.startsWith('wireWrite_'));
      if(!wireNode)throw Error('Library adapter did not create a real editable visual node');
      const addressField=document.querySelector('#nodeInspector [data-param="address"]');
      if(!addressField)throw Error('Curated Wire node has no editable I2C address');
      addressField.value='0x3D';addressField.dispatchEvent(new Event('input',{bubbles:true}));
      document.getElementById('save').click();
      await pause(350);
      const wireGenerated=await api.generate(await api.openProject(saved.id));
      if(!wireGenerated.source?.includes('Wire.beginTransmission((uint8_t)61)'))throw Error('Wire visual edit did not generate real Arduino library call');

      // User-visible sensor-to-variable-to-output workflow, including project persistence.
      document.querySelector('[data-tab="variables"]').click();
      if(document.getElementById('variablesView').classList.contains('hidden'))throw Error('Variables editor absent');
      document.getElementById('varName').value='sensorValue';
      document.getElementById('varType').value='long';
      document.getElementById('varInitial').value='0';
      document.getElementById('varAdd').click();
      for(let i=0;i<40&&!document.getElementById('variableList').textContent.includes('sensorValue');i++)await pause(50);
      if(!document.getElementById('variableList').textContent.includes('sensorValue'))throw Error('Variable manager did not create typed declaration');
      document.querySelector('[data-add="readAnalog"]').click();
      document.querySelector('[data-add="thresholdOutput"]').click();
      document.getElementById('save').click();
      await pause(650);
      const sensorProject=await api.openProject(saved.id);
      if(sensorProject.variables?.[0]?.name!=='sensorValue'||!sensorProject.graph.nodes.some(n=>n.type==='readAnalog')||!sensorProject.graph.nodes.some(n=>n.type==='thresholdOutput'))throw Error('Variable and ADC threshold blocks not persisted');
      const sensorGenerated=await api.generate(sensorProject);
      if(!sensorGenerated.source?.includes('blazeVar_sensorValue = analogRead(A0)')||!sensorGenerated.source?.includes('digitalWrite(8, (blazeVar_sensorValue >= 512L) ? HIGH : LOW)'))throw Error('Variable sensor pipeline not compiled into firmware source');
      // GUI exercise of persisted explicit typed sockets. No model-only substitute.
      document.querySelector('[data-tab="graph"]').click();
      const outputSocket=[...document.querySelectorAll('[data-data-output]')].find(n=>n.dataset.dataOutput===sensorProject.graph.nodes.find(n=>n.type==='readAnalog').id);
      const inputSocket=[...document.querySelectorAll('[data-data-input]')].find(n=>n.dataset.dataInput===sensorProject.graph.nodes.find(n=>n.type==='thresholdOutput').id);
      if(!outputSocket||!inputSocket)throw Error('Scalar output/input sockets missing from the visible GUI');
      outputSocket.click();inputSocket.click();
      for(let i=0;i<50&&!document.querySelector('#nodeInspector .dataBinding');i++)await pause(100);
      if(!document.querySelector('#nodeInspector .dataBinding'))throw Error('Data port connection not reflected in inspector');
      // Native port-drag handlers must also work: disconnect, drag and reconnect.
      const disconnect=document.getElementById('disconnectData');
      if(!disconnect)throw Error('Connected socket cannot be disconnected from inspector');
      disconnect.click();
      if(document.querySelector('#nodeInspector .dataBinding'))throw Error('Disconnected input still shown as wired');
      const dragOut=[...document.querySelectorAll('[data-data-output]')].find(n=>n.dataset.dataOutput===sensorProject.graph.nodes.find(n=>n.type==='readAnalog').id);
      const dragIn=[...document.querySelectorAll('[data-data-input]')].find(n=>n.dataset.dataInput===sensorProject.graph.nodes.find(n=>n.type==='thresholdOutput').id);
      const wireTransfer=new DataTransfer();
      dragOut.dispatchEvent(new DragEvent('dragstart',{bubbles:true,cancelable:true,dataTransfer:wireTransfer}));
      dragIn.dispatchEvent(new DragEvent('dragover',{bubbles:true,cancelable:true,dataTransfer:wireTransfer}));
      dragIn.dispatchEvent(new DragEvent('drop',{bubbles:true,cancelable:true,dataTransfer:wireTransfer}));
      for(let i=0;i<50&&!document.querySelector('#nodeInspector .dataBinding');i++)await pause(100);
      if(!document.querySelector('#nodeInspector .dataBinding'))throw Error('Native data-port drag handlers did not reconnect');
      document.getElementById('save').click();await pause(500);
      const wiredProject=await api.openProject(saved.id);
      if(wiredProject.graph.dataEdges?.length!==1||wiredProject.graph.dataEdges[0].out!=='value')throw Error('Typed data connection was not persisted through desktop project save');
      if(!(await api.generate(wiredProject)).source.includes('blazeVar_sensorValue >= 512L'))throw Error('Connected data input not present in firmware');
      const sensorVirtual=await api.simCreate(sensorProject,{});
      await api.simAnalog(sensorVirtual.id,{A0:700});
      const sensorTrace=await api.simRun(sensorVirtual.id,100);
      if(sensorTrace.variables.sensorValue!==700||sensorTrace.outputs['8']!=='HIGH')throw Error('Simulated analog threshold did not drive output');
      await api.simDispose(sensorVirtual.id);

      const espCreated=await api.createProject('ReviewedESP','esp32:esp32:esp32','blink');
      const espSource=await api.generate(espCreated);
      if(!espSource.source?.includes('pinMode(21, OUTPUT)'))throw Error('ESP32 safe default pin missing from generated sketch');
      await openProject(espCreated.id);
      document.querySelector('[data-tab="pins"]').click();
      for(let i=0;i<50&&!document.getElementById('pinGrid').textContent.includes('INPUT ONLY');i++)await pause(100);
      if(!document.getElementById('pinGrid').textContent.includes('GPIO34')||!document.getElementById('pinGrid').textContent.includes('FLASH / NO-GO'))throw Error('ESP32 Pin Manager failed to show input-only / reserved pins');
      if((await api.boardProfile('esp32:esp32:esp32s3'))!==null)throw Error('Classic ESP32 profile incorrectly claimed on S3');

      // Exercise real sidebar handlers and project tabs, not workspace data APIs alone.
      await openProject(saved.id); // Earlier ESP Pin Manager smoke intentionally changed the active project.
      const oldPrompt=window.prompt;
      window.prompt=()=>'CI Home Workspace';
      document.getElementById('workspaceCreate').click();
      await pause(400);
      window.prompt=oldPrompt;
      const workspaceList=await api.listWorkspaces();
      const ws=workspaceList.find(w=>w.name==='CI Home Workspace');
      if(!ws||document.getElementById('workspaceSelect').value!==ws.id)throw Error('New workspace UI did not persist/select collection');
      document.getElementById('workspaceAddCurrent').click();
      await pause(350);
      if(!(await api.listWorkspaces()).find(w=>w.id===ws.id)?.projectIds.includes(saved.id))throw Error('Workspace UI did not link existing project');
      const other=await api.createProject('GatewayTab','esp32:esp32:esp32');
      await api.addToWorkspace(ws.id,other.id);
      await refreshWorkspaces();await refreshProjects(false);
      const otherButton=document.querySelector('#projectList [data-open="'+other.id+'"]');
      if(!otherButton)throw Error('Workspace project not visible in scoped sidebar');
      otherButton.click();
      for(let i=0;i<30&&document.getElementById('projectTitle').textContent!=='GatewayTab';i++)await pause(80);
      if(document.getElementById('projectTitle').textContent!=='GatewayTab')throw Error('Second project did not open in tab');
      const tabFirst=document.querySelector('#openProjectTabs [data-activate-project="'+saved.id+'"]');
      if(!tabFirst)throw Error('First project tab lost after opening second');
      tabFirst.click();
      for(let i=0;i<30&&document.getElementById('projectTitle').textContent!=='GuiSmoke';i++)await pause(80);
      if(document.getElementById('projectTitle').textContent!=='GuiSmoke')throw Error('Project tab switching failed');
      if((await api.openProject(saved.id)).fqbn!=='arduino:avr:uno'||(await api.openProject(other.id)).fqbn!=='esp32:esp32:esp32')throw Error('Workspace leaked board identity');
      document.getElementById('workspaceRemoveCurrent').click();await pause(350);
      if((await api.listWorkspaces()).find(w=>w.id===ws.id)?.projectIds.includes(saved.id))throw Error('UI unlink did not persist');
      await api.deleteWorkspace(ws.id);
      if((await api.listWorkspaces()).some(w=>w.id===ws.id))throw Error('Workspace deletion failed');
      if(!(await api.openProject(saved.id))||!(await api.openProject(other.id)))throw Error('Workspace deletion altered project firmware');
      // Real IPC persistence and renderer rehydration, not only schema unit tests.
      const sessionLayout=await api.getSession();
      if(sessionLayout.workspaceId!==''||sessionLayout.activeProjectId!==saved.id
       ||!sessionLayout.openProjectIds.includes(saved.id)||!sessionLayout.openProjectIds.includes(other.id))
       throw Error('Desktop session did not preserve active target and valid independent tabs');
      await restoreSession();
      if(document.getElementById('projectTitle').textContent!=='GuiSmoke'
       ||!document.querySelector('#openProjectTabs [data-activate-project="'+other.id+'"]'))
       throw Error('Desktop session restore did not rehydrate real renderer tabs');

      const created=await api.createProject('CISmoke','arduino:avr:uno');
      const reopened=await api.openProject(created.id);
      const generated=await api.generate(reopened);
      if(!generated.source?.includes('digitalWrite(13, HIGH)'))throw Error('Generator not wired through preload');
      const sim=await api.simCreate(reopened,{});
      const trace=await api.simRun(sim.id,30);
      if(trace.outputs['13']!=='LOW'||trace.virtualTimeMs!==2000)throw Error('Simulator output mismatch');
      const resources=await api.resourceAnalyze(reopened,null,{intervalSeconds:10,bytesPerRecord:48,capacityBytes:1048576,retentionDays:7});
      if(resources.storage.recordsDay!==8640)throw Error('Resource advisor IPC mismatch');
      return {passed:true,renderer:true,ipc:true,boardCatalog:true,newProjectUI:true,paletteDragDrop:true,inspectorEdit:true,persistence:true,generation:true,curatedWireGUI:true,workspaceTabUI:true,sessionRestoreUI:true,typedVariableUI:true,analogThresholdFirmware:true,analogSimulation:true,reviewedEspGpioUI:true,typedDataLinkGUI:true,typedDataDragGUI:true,simulation:true,resources:true};
    })()`);
   }catch(e){report={passed:false,error:String(e?.stack||e)};}
   try{fs.writeFileSync(process.env.BLAZE_MCU_SMOKE_FILE,JSON.stringify(report,null,2));}catch(e){console.error('SMOKE REPORT WRITE FAILED',e);}
   setTimeout(()=>app.quit(),500);
  });
 }
}

module.exports = { installGuiSmoke };
