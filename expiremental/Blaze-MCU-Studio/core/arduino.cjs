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
// These are installation entry points, NOT an invented catalog of installed boards.
// After core installation, all actual board definitions are obtained from Arduino CLI.
const STARTER_TARGETS=Object.freeze([
 {name:'Arduino Uno Rev3',fqbn:'arduino:avr:uno',core:'arduino:avr'},
 {name:'Arduino Mega 2560',fqbn:'arduino:avr:mega',core:'arduino:avr'},
 {name:'Arduino Nano (ATmega328P)',fqbn:'arduino:avr:nano',core:'arduino:avr'},
 {name:'ESP8266 Generic',fqbn:'esp8266:esp8266:generic',core:'esp8266:esp8266'},
 {name:'NodeMCU 1.0 ESP-12E',fqbn:'esp8266:esp8266:nodemcuv2',core:'esp8266:esp8266'},
 {name:'ESP32 Dev Module',fqbn:'esp32:esp32:esp32',core:'esp32:esp32'},
 {name:'ESP32-S3 Dev Module',fqbn:'esp32:esp32:esp32s3',core:'esp32:esp32'}
]);
const CORE_URLS=Object.freeze({
 'esp8266:esp8266':'https://arduino.esp8266.com/stable/package_esp8266com_index.json',
 'esp32:esp32':'https://espressif.github.io/arduino-esp32/package_esp32_index.json'
});
function parseBoardCatalog(stdout){
 const obj=JSON.parse(stdout);
 const actual=Array.isArray(obj)?obj:Array.isArray(obj.boards)?obj.boards:[];
 return actual.map(b=>({name:b.name||b.fqbn,fqbn:b.fqbn,core:String(b.fqbn||'').split(':').slice(0,2).join(':'),installed:true,status:'Installed core'}))
 .filter(b=>typeof b.fqbn==='string'&&FQBN_RE.test(b.fqbn));
}
function combineBoards(actual){
 const found=new Map(actual.map(b=>[b.fqbn,{...b,installed:true,status:'Installed core'}]));
 for(const b of STARTER_TARGETS)if(!found.has(b.fqbn))found.set(b.fqbn,{...b,installed:false,status:'Starter target — install its core to compile'});
 return [...found.values()].sort((a,b)=>Number(b.installed)-Number(a.installed)||a.name.localeCompare(b.name));
}
async function boardList(binary){
 const r=await run(binary,['board','listall','--json']);
 if(!r.ok)return {...r,boards:STARTER_TARGETS.map(b=>({...b,installed:false,status:'Core installation required'})),catalogReady:false};
 try{const installed=parseBoardCatalog(r.stdout);return {...r,boards:combineBoards(installed),installedCount:installed.length,catalogReady:true};}
 catch(e){return {...r,ok:false,stderr:'Invalid Arduino CLI board JSON: '+e.message+' '+r.stderr,boards:[],catalogReady:false};}
}
async function coreSearch(binary){
 const r=await run(binary,['core','search','--json'],{timeout:60000});
 if(!r.ok)return {...r,cores:[]};
 try{const value=JSON.parse(r.stdout),items=Array.isArray(value)?value:(value.platforms||value.cores||[]);
  return {...r,cores:items.map(x=>({id:x.id||x.platform?.id||'',name:x.name||x.platform?.name||'',version:x.latest_version||x.latestVersion||''})).filter(x=>ID.test(x.id))};}
 catch(e){return {...r,ok:false,cores:[],stderr:'Invalid core search data: '+e.message};}
}
async function platformInstall(binary,id){
 if(typeof id!=='string'||!ID.test(id))throw new Error('Invalid core identifier');
 const core=id.split('@')[0],url=CORE_URLS[core];
 // Pass official indexes per invocation instead of silently changing global Arduino settings.
 const urls=url?['--additional-urls',url]:[];
 const updated=await run(binary,['core','update-index',...urls],{timeout:180000});
 if(!updated.ok)return {...updated,phase:'index-update'};
 return {...await run(binary,['core','install',id,...urls],{timeout:600000}),phase:'core-install'};
}
async function compile(binary,p){const built=generateSketch(p);if(!built.source||!built.source.trim())return {ok:false,exitCode:-3,stdout:'',stderr:built.diagnostics.errors.join('\n')||'Empty source'};
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'blaze-mcu-'));const basename=sketchName(p.name);const dir=path.join(root,basename);fs.mkdirSync(dir);const filename=path.join(dir,basename+'.ino');fs.writeFileSync(filename,built.source,'utf8');
 try{return {...await run(binary,['compile','--fqbn',p.fqbn,'--warnings','all',dir],{timeout:300000}),source:built.source,diagnostics:built.diagnostics};}finally{fs.rmSync(root,{recursive:true,force:true});}}
module.exports={findCli,run,boardList,coreSearch,parseBoardCatalog,combineBoards,platformInstall,compile,STARTER_TARGETS,CORE_URLS};
