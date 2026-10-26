'use strict';
const {spawn}=require('node:child_process'); const path=require('node:path');const fs=require('node:fs');const os=require('node:os');
const {generateSketch,sketchName,FQBN_RE}=require('./project.cjs');
const ID=/^[\w.-]+:[\w.-]+(?:@[\w.+-]+)?$/;
function findCli(resourcesPath){
  const names=process.platform==='win32'?['arduino-cli.exe']:['arduino-cli'];
  for(const name of names){for(const dir of [resourcesPath&&path.join(resourcesPath,'bin'),process.env.BLAZE_ARDUINO_CLI_DIR]){if(dir){const candidate=path.join(dir,name);if(fs.existsSync(candidate))return candidate;}}}
  return names[0];
}
function run(binary,args,{timeout=120000}={}){return new Promise((resolve)=>{let stdout='',stderr='',done=false;let child;
  try{child=spawn(binary,args,{windowsHide:true,shell:false,stdio:['ignore','pipe','pipe'],env:{...process.env,NO_COLOR:'1'}})}catch(e){resolve({ok:false,exitCode:-1,stdout:'',stderr:e.message});return;}
  const finish=(exitCode,extra='')=>{if(done)return;done=true;clearTimeout(timer);resolve({ok:exitCode===0,exitCode,stdout,stderr:stderr+extra,command:[binary,...args]});};
  const add=(key,chunk)=>{const limit=2_000_000;if(key==='out')stdout=(stdout+chunk.toString('utf8')).slice(-limit);else stderr=(stderr+chunk.toString('utf8')).slice(-limit);};
  child.stdout.on('data',d=>add('out',d));child.stderr.on('data',d=>add('err',d));
  child.on('error',e=>finish(-1,'\n'+e.message));child.on('close',code=>finish(code??-1));
  const timer=setTimeout(()=>{child.kill();finish(-2,'\nTimed out after '+timeout+'ms')},timeout);});}
async function boardList(binary){const r=await run(binary,['board','listall','--json']); if(!r.ok)return {...r,boards:[]};try{const obj=JSON.parse(r.stdout);return {...r,boards:(obj.boards||[]).map(b=>({name:b.name,fqbn:b.fqbn})).filter(b=>typeof b.fqbn==='string'&&FQBN_RE.test(b.fqbn))};}catch{return {...r,ok:false,stderr:'Invalid Arduino CLI JSON: '+r.stderr,boards:[]}}}
async function platformInstall(binary,id){if(typeof id!=='string'||!ID.test(id))throw new Error('Invalid core identifier');const r=await run(binary,['core','update-index'],{timeout:180000});if(!r.ok)return r;return run(binary,['core','install',id],{timeout:600000});}
async function compile(binary,p){const built=generateSketch(p);if(!built.source||!built.source.trim())return {ok:false,exitCode:-3,stdout:'',stderr:built.diagnostics.errors.join('\n')||'Empty source'};
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'blaze-mcu-'));const basename=sketchName(p.name);const dir=path.join(root,basename);fs.mkdirSync(dir);const filename=path.join(dir,basename+'.ino');fs.writeFileSync(filename,built.source,'utf8');
 try{return {...await run(binary,['compile','--fqbn',p.fqbn,'--warnings','all',dir],{timeout:300000}),source:built.source,diagnostics:built.diagnostics};}finally{fs.rmSync(root,{recursive:true,force:true});}}
module.exports={findCli,run,boardList,platformInstall,compile};
