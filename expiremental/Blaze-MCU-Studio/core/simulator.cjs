'use strict';
// Deterministic source-model logic simulator. No firmware CPU, voltage or peripheral emulation.
const {randomUUID}=require('node:crypto');
const {generateSketch,analyzeGraph,verifyProject}=require('./project.cjs');
const flow=require('./flowchart.cjs');
const variables=require('./variables.cjs');
const dataLinks=require('./data-links.cjs');
const MAX_STEPS=20000, MAX_EVENTS=300;
const VALID_PIN=/^\d{1,3}$/;
function normalizeInputs(inputs={}){
 if(!inputs||typeof inputs!=='object'||Array.isArray(inputs)||Object.keys(inputs).length>64)throw Error('Invalid virtual GPIO inputs');
 const out={};for(const [pin,value] of Object.entries(inputs)){
  if(!VALID_PIN.test(pin)||!['HIGH','LOW'].includes(value))throw Error('Virtual GPIO input must be D0-D999 HIGH or LOW');out[pin]=value;
 }return out;
}
function preview(s){
 const next=peekStep(s)?.id||null;
 return {id:s.id,mode:s.mode,status:s.status,virtualTimeMs:s.time,stepCount:s.count,next,outputs:{...s.outputs},inputs:{...s.inputs},pinModes:{...s.pinModes},pwm:{...s.pwm},analogInputs:{...s.analogInputs},variables:{...s.variables},lastEvent:s.events.at(-1)||null,events:s.events.slice(),warnings:s.warnings.slice(),breakpoints:s.breakpoints.slice()};
}
function frame(steps,repeat=1){return {steps,index:0,remaining:repeat};}
function nextStep(s){while(s.frames.length){const top=s.frames.at(-1);if(top.index<top.steps.length)return top.steps[top.index++];if(--top.remaining>0){top.index=0;continue;}s.frames.pop();}return null;}
function peekStep(s){for(let i=s.frames.length-1;i>=0;i--){const f=s.frames[i];if(f.index<f.steps.length)return f.steps[f.index];if(f.remaining>1&&f.steps.length)return f.steps[0];}return null;}
class SimulationController {
 constructor(){this.sessions=new Map();}
 create(project,inputs={}){
  verifyProject(project);if(project.source.mode==='manual')throw Error('Manual C++ cannot be simulated by the visual logic interpreter');
  const gen=generateSketch(project);if(!gen.diagnostics.ok)throw Error('Resolve source validation before simulation: '+gen.diagnostics.errors.join('; '));
  if(this.sessions.size>=12)this.sessions.delete(this.sessions.keys().next().value);
  const mode=project.visualMode==='flowchart'?'flowchart':'nodes';
  const ordered=mode==='nodes'?analyzeGraph(project).ordered:[];
  const wired=mode==='nodes'?dataLinks.plan(project,ordered):null;
  const steps=mode==='flowchart'?(project.flowchart?.steps||[]):ordered.map(n=>{const effective=dataLinks.effectiveNode(n,wired);return {id:n.id,type:n.type,params:effective.params};});
  const s={id:randomUUID(),mode,status:'ready',frames:[frame(steps)],inputs:normalizeInputs(inputs),outputs:{},pinModes:{},pwm:{},analogInputs:{},variables:variables.initialState(project.variables||[]),variableTypes:Object.fromEntries((project.variables||[]).map(v=>[v.name,v.type])),time:0,count:0,events:[],warnings:['Logic model only: virtual GPIO does not emulate physical circuitry or MCU firmware.'],breakpoints:[],skipOnce:false};
  this.sessions.set(s.id,s);return preview(s);
 }
 get(id){const s=this.sessions.get(id);if(!s)throw Error('Simulation session expired; reset simulation');return s;}
 inputs(id,inputs){const s=this.get(id);s.inputs=normalizeInputs(inputs);return preview(s);}
 analog(id,inputs){const s=this.get(id);if(!inputs||typeof inputs!=='object'||Array.isArray(inputs)||Object.keys(inputs).length>6)throw Error('Invalid virtual analog input map');const out={};for(const [pin,value] of Object.entries(inputs)){if(!/^A[0-5]$/.test(pin)||!Number.isInteger(value)||value<0||value>1023)throw Error('Virtual Uno analog input must be A0–A5 with integer 0..1023');out[pin]=value;}s.analogInputs=out;return preview(s);}
 breakpoints(id,ids){const s=this.get(id);if(!Array.isArray(ids)||ids.length>100||ids.some(x=>typeof x!=='string'||!/^[A-Za-z][\w]{0,63}$/.test(x)))throw Error('Invalid breakpoints');s.breakpoints=[...new Set(ids)];return preview(s);}
 step(id,{respectBreakpoint=false}={}){const s=this.get(id);if(s.status==='done'||s.status==='limit')return preview(s);if(s.count>=MAX_STEPS){s.status='limit';return preview(s);}
  const top=peekStep(s);if(top&&respectBreakpoint&&s.breakpoints.includes(top.id)&&!s.skipOnce){s.status='paused';s.skipOnce=true;return preview(s);}
  s.skipOnce=false;const n=nextStep(s);if(!n){s.status='done';return preview(s);}s.status='running';s.count++;
  const p=n.params||{};let effect='';const pin=String(p.pin??'');
  switch(n.type){
   case 'loopStart':effect='loop-entry';break;
   case 'setOutput':s.pinModes[pin]='OUTPUT';effect='configure D'+pin+' OUTPUT';break;
   case 'pinMode':s.pinModes[pin]=p.mode;effect='configure D'+pin+' '+p.mode;break;
   case 'digitalWrite':case 'write':s.outputs[pin]=p.value;effect='D'+pin+'='+p.value;break;
   case 'branch':{const actual=s.inputs[pin]||'LOW';const yes=actual===p.equals;s.frames.push(frame(yes?n.thenSteps||[]:n.elseSteps||[]));effect='D'+pin+'='+actual+' → '+(yes?'YES':'NO')+(pin in s.inputs?'':' (unspecified input assumed LOW)');break;}
   case 'repeat':s.frames.push(frame(n.thenSteps||[],Number(p.count)));effect='repeat '+p.count+' times';break;
   case 'setVariable': {const type=s.variableTypes[p.target];s.variables[p.target]=type==='bool'?p.value==='true':Number(p.value);effect=p.target+' = '+String(s.variables[p.target]);break;}
   case 'readAnalog': {const value=s.analogInputs[p.pin]??0;s.variables[p.target]=value;effect=p.target+' = '+value+' from virtual '+p.pin+(p.pin in s.analogInputs?'':' (unset: simulated zero)');break;}
   case 'thresholdOutput': {const val=s.variables[p.variable],ref=Number(p.threshold);const yes=({'<':()=>val<ref,'<=':()=>val<=ref,'>':()=>val>ref,'>=':()=>val>=ref,'==':()=>val===ref,'!=':()=>val!==ref})[p.operator]();s.outputs[pin]=yes?p.trueValue:p.falseValue;effect=p.variable+' '+p.operator+' '+p.threshold+' → '+(yes?'YES':'NO')+', D'+pin+'='+s.outputs[pin];break;}
   case 'pwmWrite':s.pinModes[pin]='OUTPUT';s.pwm[pin]=Number(p.value);effect='virtual D'+pin+' PWM '+p.value+'/255';break;
   case 'serialPrint':effect='virtual Serial.println('+JSON.stringify(p.text)+'); no UART emulation';break;
   case 'wireWrite':effect='Wire I2C transaction request; ACK and device result NOT emulated';if(!s.warnings.includes('Wire I2C response requires a hardware model'))s.warnings.push('Wire I2C response requires a hardware model');break;
   case 'delay':case 'wait':s.time+=Number(p.ms);effect='virtual delay '+p.ms+'ms';break;
   case 'callNodes':effect='node-graph call not emulated';s.warnings.push('callNodes requires its own simulation; this trace does not execute that call');break;
   case 'end':s.frames.length=0;effect='return to outer loop';break;
   case 'comment':case 'note':effect='comment';break;
   default:throw Error('Unsupported logic node '+n.type);
  }
  s.events.push({number:s.count,id:n.id,type:n.type,effect,timeMs:s.time,outputs:{...s.outputs}});
  if(s.events.length>MAX_EVENTS)s.events.shift();if(!peekStep(s))s.status='done';return preview(s);
 }
 run(id,{maxSteps=1000}={}){if(!Number.isSafeInteger(maxSteps)||maxSteps<1||maxSteps>5000)throw Error('Run budget must be 1..5000');
  let out;for(let i=0;i<maxSteps;i++){out=this.step(id,{respectBreakpoint:true});if(['paused','done','limit'].includes(out.status))break;}
  if(out&&out.status==='running') {this.get(id).status='paused';out=preview(this.get(id));}return out;
 }
 dispose(id){this.sessions.delete(id);return {disposed:true};}
}
module.exports={SimulationController,normalizeInputs,MAX_STEPS};
