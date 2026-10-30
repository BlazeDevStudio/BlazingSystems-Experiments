'use strict';const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');const root=path.join(__dirname,'../renderer');
test('all static UI selectors reference existing unique elements',()=>{const app=fs.readFileSync(path.join(root,'app.js'),'utf8'),html=fs.readFileSync(path.join(root,'index.html'),'utf8');const refs=[...app.matchAll(/\$\('(#[A-Za-z\d_-]+)'\)/g)].map(m=>m[1].slice(1));const all=[...html.matchAll(/\bid="([A-Za-z\d_-]+)"/g)].map(m=>m[1]),ids=new Set(all);assert.equal(ids.size,all.length);for(const id of refs)assert(ids.has(id),'Missing UI element '+id);});
test('flowchart and library editor tabs have dedicated views',()=>{const html=fs.readFileSync(path.join(root,'index.html'),'utf8');for(const token of ['data-tab="flowchart"','id="flowchartView"','data-tab="libraries"','id="librariesView"','id="manualMode"'])assert(html.includes(token));});
test('typed state UI has a complete input and inspector surface',()=>{const html=fs.readFileSync(path.join(root,'index.html'),'utf8'),app=fs.readFileSync(path.join(root,'app.js'),'utf8');for(const id of ['variablesView','varName','varType','varInitial','varAdd','variableList','simAnalogPin','simAnalogValue','simSetAnalog','simVariables','newTemplate'])assert(html.includes(`id="${id}"`),id);for(const kind of ['setVariable','readAnalog','thresholdOutput'])assert(html.includes(`data-add="${kind}"`),kind);assert(app.includes('renderVariables()'));assert(app.includes('window.blaze.simAnalog'));});

test('workspace collection and multi-project tab controls are actually addressable',()=>{const html=fs.readFileSync(path.join(root,'index.html'),'utf8'),app=fs.readFileSync(path.join(root,'app.js'),'utf8');for(const id of ['workspaceSelect','workspaceCreate','workspaceRename','workspaceDelete','workspaceAddCurrent','workspaceRemoveCurrent','workspaceSummary','openProjectTabs'])assert(html.includes(`id="${id}"`),id);for(const api of ['window.blaze.createWorkspace','window.blaze.addToWorkspace','window.blaze.removeFromWorkspace','window.blaze.deleteWorkspace'])assert(app.includes(api),api);});

test('desktop tab persistence is wired through secure IPC, restore path and UI handlers',()=>{
 const electron=fs.readFileSync(path.join(__dirname,'../electron/main.cjs'),'utf8');
 const preload=fs.readFileSync(path.join(__dirname,'../electron/preload.cjs'),'utf8');
 const app=fs.readFileSync(path.join(root,'app.js'),'utf8');
 for(const id of ["'session:load'","'session:save'"])assert(electron.includes(id),id);
 for(const name of ["getSession:'session:load'","saveSession:'session:save'"])assert(preload.includes(name),name);
 assert(app.includes('async function restoreSession()'));
 assert(app.includes('await restoreSession();'));
 assert(app.includes('await persistSession();'));
 assert(electron.includes('sessionRestoreUI:true'));
});
