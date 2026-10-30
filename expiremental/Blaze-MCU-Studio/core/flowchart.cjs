'use strict';
// Flowchart owns only structured visual program logic. Arbitrary C++ always remains user-owned.
const TYPES = Object.freeze(['setOutput','write','wait','branch','repeat','note','callNodes','end']);
const NAME=/^[A-Za-z][\w]{0,63}$/;
const PIN=/^\d{1,3}$/;
const LEVEL=new Set(['HIGH','LOW']);
function step(id,type,params={},thenSteps=[],elseSteps=[]){return {id,type,params,thenSteps,elseSteps};}
function sampleFlowchart(pin='13'){return {steps:[step('pinsetup','setOutput',{pin}),step('on','write',{pin,value:'HIGH'}),step('pause1','wait',{ms:1000}),step('off','write',{pin,value:'LOW'}),step('pause2','wait',{ms:1000})]};}
function ensureFlowchart(flow){if(!flow||!Array.isArray(flow.steps))throw Error('Missing flowchart steps');const seen=new Set();let count=0;
 function visit(list,depth){if(depth>12)throw Error('Flowchart nesting exceeds 12 levels');if(!Array.isArray(list))throw Error('Malformed flowchart step list');for(const n of list){if(++count>400)throw Error('Flowchart exceeds 400 blocks');if(!n||!NAME.test(n.id)||seen.has(n.id)||!TYPES.includes(n.type)||!n.params||typeof n.params!=='object'||Array.isArray(n.params))throw Error('Invalid flowchart block');seen.add(n.id);const p=n.params;
 if(['setOutput','write','branch'].includes(n.type)&&!PIN.test(String(p.pin??'')))throw Error(n.id+': invalid pin identifier');
 if(n.type==='write'&&!LEVEL.has(p.value))throw Error(n.id+': invalid output level');
 if(n.type==='branch'&&!LEVEL.has(p.equals))throw Error(n.id+': invalid branch comparison');
 if(n.type==='wait'&&(!Number.isSafeInteger(Number(p.ms))||Number(p.ms)<0||Number(p.ms)>4294967295))throw Error(n.id+': invalid delay');
 if(n.type==='repeat'&&(!Number.isSafeInteger(Number(p.count))||Number(p.count)<1||Number(p.count)>10000))throw Error(n.id+': repeat count must be 1–10000');
 if(n.type==='note'&&typeof p.text!=='string')throw Error(n.id+': invalid comment');
 if(n.type!=='branch'&&n.elseSteps?.length)throw Error(n.id+': alternate execution requires branch');
 if(n.type!=='branch'&&n.type!=='repeat'&&n.thenSteps?.length)throw Error(n.id+': nested execution requires branch/repeat');
 visit(n.thenSteps||[],depth+1);visit(n.elseSteps||[],depth+1);
 }}visit(flow.steps,0);return true;}
function usedPins(flow){ensureFlowchart(flow);const pins=[];function walk(items){for(const n of items){if(['setOutput','write','branch'].includes(n.type))pins.push({id:n.id,pin:String(n.params.pin),direction:n.type==='branch'?'input':'output'});walk(n.thenSteps||[]);walk(n.elseSteps||[]);}}walk(flow.steps);return pins;}
function validateFlowchart(flow,{boardPins,boardFqbn}={}){const errors=[],warnings=[];try{ensureFlowchart(flow);}catch(e){return {ok:false,errors:[e.message],warnings};}
 const board=require('./board.cjs');const pins=usedPins(flow);
 for(const pin of pins){
  const check=board.pinCheck(boardFqbn||'unknown:unknown:unknown',pin.pin,pin.direction);
  errors.push(...check.errors.map(message=>pin.id+': '+message));
  warnings.push(...check.warnings.map(message=>pin.id+': '+message));
 }
 return {ok:errors.length===0,errors:[...new Set(errors)],warnings:[...new Set(warnings)]};}
function flowchartSource(flow){ensureFlowchart(flow);const setup=[],loop=[];let counter=0;let needsNodeCall=false;
 const readPins=[...new Set(usedPins(flow).filter(p=>p.direction==='input').map(p=>p.pin))];const outputPins=new Set(usedPins(flow).filter(p=>p.direction==='output').map(p=>p.pin));for(const pin of readPins){if(!outputPins.has(pin))setup.push('  pinMode('+Number(pin)+', INPUT); // flow:auto-input');}
 function emit(list,lines,indent='  '){for(const n of list){const p=n.params,pin=Number(p.pin),comment=` // flow:${n.id}`;
 switch(n.type){case 'setOutput':setup.push('  pinMode('+pin+', OUTPUT);'+comment);break;
 case 'write':lines.push(indent+'digitalWrite('+pin+', '+p.value+');'+comment);break;
 case 'wait':lines.push(indent+'delay('+Number(p.ms)+'UL);'+comment);break;
 case 'note':lines.push(indent+'// '+String(p.text).replace(/[\r\n]/g,' ').replace(/\*\//g,'')+comment);break;
 case 'branch':lines.push(indent+'if (digitalRead('+pin+') == '+p.equals+') {'+comment);emit(n.thenSteps||[],lines,indent+'  ');lines.push(indent+'} else {');emit(n.elseSteps||[],lines,indent+'  ');lines.push(indent+'}');break;
 case 'repeat':{const v='_blaze_repeat_'+counter++;lines.push(indent+'for (unsigned long '+v+' = 0; '+v+' < '+Number(p.count)+'UL; ++'+v+') {'+comment);emit(n.thenSteps||[],lines,indent+'  ');lines.push(indent+'}');break;}
 case 'callNodes':needsNodeCall=true;lines.push(indent+'blazeNodesTick();'+comment);break;
 case 'end': lines.push(indent+'return;'+comment);break;
 }} }
 emit(flow.steps,loop);return {setup,loop,needsNodeCall};}
function traceFlowchart(flow,input={},limit=1000){ensureFlowchart(flow);const events=[],pins={},read=(pin)=>input[String(pin)]==='HIGH'?'HIGH':'LOW';let budget=limit;
 function run(steps){for(const n of steps){if(--budget<0)throw Error('Trace step budget exceeded');const p=n.params;events.push({id:n.id,type:n.type,pins:{...pins}});
 switch(n.type){case 'setOutput':break;case 'write':pins[p.pin]=p.value;break;case 'branch':run(read(p.pin)===p.equals?n.thenSteps||[]:n.elseSteps||[]);break;case 'repeat':for(let i=0;i<Number(p.count);i++)run(n.thenSteps||[]);break;case 'end':return true;case 'callNodes':events.push({id:n.id,type:'external-node-call',status:'not-emulated'});break;} }return false;}
 try{run(flow.steps);return {ok:true,events,pins,model:'logic trace only; no hardware emulation'};}catch(e){return {ok:false,events,error:e.message,model:'logic trace only'};}}
module.exports={TYPES,step,sampleFlowchart,ensureFlowchart,usedPins,validateFlowchart,flowchartSource,traceFlowchart};
