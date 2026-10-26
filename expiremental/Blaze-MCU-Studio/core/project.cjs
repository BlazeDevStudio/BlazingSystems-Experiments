'use strict';
const { randomUUID } = require('node:crypto');
const SCHEMA_VERSION = 1;
const flow=require('./flowchart.cjs');
const peripherals=require('./peripherals.cjs');
const wire=require('./curated-adapters.cjs');
const NAME_RE = /^[A-Za-z][A-Za-z0-9_]{0,62}$/;
const FQBN_RE = /^[\w.-]+:[\w.-]+:[\w.-]+(?::[\w.,=~-]+)?$/;
function sketchName(text) {
  const result = String(text || 'Sketch').replace(/[^A-Za-z0-9_]/g, '_').replace(/^[^A-Za-z]+/, 'S');
  return result.substring(0, 60) || 'Sketch';
}
function node(id, type, params, x, y) { return { id, type, params, x, y }; }
function starterGraph() { return {
  nodes: [node('start', 'loopStart', {}, 70, 100), node('mode', 'pinMode', { pin: '13', mode: 'OUTPUT' }, 320, 90), node('on', 'digitalWrite', { pin: '13', value: 'HIGH' }, 570, 90), node('wait1', 'delay', { ms: 1000 }, 810, 90), node('off', 'digitalWrite', { pin: '13', value: 'LOW' }, 570, 285), node('wait2', 'delay', { ms: 1000 }, 810, 285)],
  edges: [['start','mode'],['mode','on'],['on','wait1'],['wait1','off'],['off','wait2']]
}; }
function createProject(name, fqbn='arduino:avr:uno') {
  if (!FQBN_RE.test(fqbn)) throw new Error('Choose a valid board FQBN');
  if (!name || !String(name).trim() || String(name).trim().length > 80) throw new Error('Project name must be 1–80 characters');
  return { schemaVersion: SCHEMA_VERSION, id: randomUUID(), name: String(name).trim(), fqbn, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(), graph: starterGraph(), source: {mode:'visual',manualSource:'',userPrelude:'',userSetup:'',userLoop:''}, pins: [], libraryDependencies: [],visualMode:'nodes',flowchart:flow.sampleFlowchart(),peripherals:[] };
}
function verifyProject(p) {
  if (!p || p.schemaVersion !== SCHEMA_VERSION || !/^[0-9a-f-]{36}$/i.test(p.id) || !FQBN_RE.test(p.fqbn)) throw new Error('Invalid project metadata');
  if (typeof p.name !== 'string' || !p.name.trim() || p.name.length > 80 || !Array.isArray(p.graph?.nodes) || !Array.isArray(p.graph?.edges)) throw new Error('Malformed project graph');
  if (p.graph.nodes.length > 300 || p.graph.edges.length > 600) throw new Error('Graph limit exceeded');
  if (!p.source || !['manual','visual'].includes(p.source.mode)) throw new Error('Missing source ownership');
  for (const k of ['manualSource','userPrelude','userSetup','userLoop']) if (typeof p.source[k] !== 'string' || p.source[k].length > 500000) throw new Error('Invalid source text');
  const seen = new Set();
  for (const n of p.graph.nodes) {
    if (typeof n.id !== 'string' || !/^[A-Za-z0-9_-]{1,60}$/.test(n.id) || seen.has(n.id) || !['loopStart','pinMode','digitalWrite','delay','comment','pwmWrite','serialPrint','wireWrite'].includes(n.type) || typeof n.params !== 'object' || n.params === null) throw new Error('Invalid node');
    if (!Number.isFinite(n.x) || !Number.isFinite(n.y) || n.x < 0 || n.y < 0 || n.x > 20000 || n.y > 20000) throw new Error('Invalid node coordinates');
    seen.add(n.id);
  }
  if(p.visualMode!==undefined&&!['nodes','flowchart'].includes(p.visualMode))throw Error('Invalid visual editor mode');
  if(p.flowchart!==undefined)flow.ensureFlowchart(p.flowchart);
  if(p.peripherals!==undefined && (!Array.isArray(p.peripherals)||p.peripherals.length>40))throw Error('Invalid peripheral assignments');
  return p;
}
const PIN_PROFILES = {
  'arduino:avr:uno': { provenance:'Arduino Uno R3 ATmega328P reference / digital D0–D13, serial RX/TX D0/D1', pins: Array.from({length:14},(_,i)=>String(i)), reserved:['0','1'] }
};
function pinDiagnostics(p) {
  const errors=[], warnings=[];
  const pins=PIN_PROFILES[p.fqbn];
  const modes=new Map();
  for (const n of p.graph.nodes) {
    if (!['digitalWrite','pinMode','pwmWrite'].includes(n.type)) continue;
    const pin=String(n.params.pin ?? '').trim();
    if (!/^\d{1,3}$/.test(pin)) { errors.push(`${n.id}: GPIO must be a numeric digital pin`); continue; }
    if (pins) {
      if (!pins.pins.includes(pin)) errors.push(`${n.id}: D${pin} unavailable on Uno R3`);
      else if (pins.reserved.includes(pin)) warnings.push(`${n.id}: D${pin} shares the hardware serial interface`);
    } else warnings.push(`${n.id}: pin ${pin} compatibility unknown for ${p.fqbn}; verify the selected board pinout`);
    if(n.type==='pwmWrite' && pins && !['3','5','6','9','10','11'].includes(pin))errors.push(`${n.id}: Uno R3 hardware PWM only on D3,D5,D6,D9,D10,D11`);
    if (n.type === 'pinMode') {
      const old=modes.get(pin);
      if (old && old !== n.params.mode) errors.push(`Conflicting modes for pin ${pin}`);
      modes.set(pin, n.params.mode);
    }
  }
  if(p.visualMode==='flowchart'&&p.flowchart){const fd=flow.validateFlowchart(p.flowchart,{boardPins:pins,boardFqbn:p.fqbn});errors.push(...fd.errors);warnings.push(...fd.warnings);}
  if(p.peripherals?.length){const plan=peripherals.plan(p);errors.push(...plan.errors);warnings.push(...plan.warnings);}
  return {errors:[...new Set(errors)],warnings:[...new Set(warnings)]};
}
function analyzeGraph(p) {
  verifyProject(p);
  const errors=[], warnings=[];
  const nodes=new Map(p.graph.nodes.map(n=>[n.id,n]));
  const successors=new Map(); const incoming=new Map();
  for(const e of p.graph.edges) {
    if (!Array.isArray(e) || e.length!==2 || !nodes.has(e[0]) || !nodes.has(e[1])) {errors.push('Dangling or malformed connection'); continue;}
    const a=successors.get(e[0])||[]; a.push(e[1]); successors.set(e[0],a);
    incoming.set(e[1], (incoming.get(e[1])||0)+1);
  }
  const starts=p.graph.nodes.filter(n=>n.type==='loopStart');
  if(starts.length!==1) errors.push('Exactly one Loop Start block is required');
  const ordered=[], visited=new Set(); let cur=starts[0]?.id;
  while(cur && nodes.has(cur)) {
    if(visited.has(cur)){ errors.push('Execution cycle detected: loops require an explicit supported construct'); break; }
    visited.add(cur); ordered.push(nodes.get(cur));
    const next=successors.get(cur)||[];
    if(next.length>1) errors.push(`${cur}: multiple execution outputs are not supported in v0.1.0`);
    cur=next[0];
  }
  for(const n of p.graph.nodes) if(!visited.has(n.id)) warnings.push(`${n.id}: unreachable and will not be generated`);
  for(const [id,n] of incoming) if(n>1) errors.push(`${id}: multiple execution inputs are not supported`);
  for(const n of ordered) {
    if(n.type==='pinMode' && !['INPUT','OUTPUT','INPUT_PULLUP'].includes(n.params.mode)) errors.push(`${n.id}: invalid pin mode`);
    if(n.type==='digitalWrite' && !['HIGH','LOW'].includes(n.params.value)) errors.push(`${n.id}: invalid output level`);
    if(n.type==='delay' && (!Number.isSafeInteger(Number(n.params.ms)) || Number(n.params.ms)<0 || Number(n.params.ms)>4294967295)) errors.push(`${n.id}: delay must be 0–4294967295 milliseconds`);
  }
  for(const n of ordered){
    if(n.type==='wireWrite'){const d=wire.validate(n,p.fqbn);errors.push(...d.errors);warnings.push(...d.warnings);}
    if(n.type==='pwmWrite'&&(!/^\d{1,3}$/.test(String(n.params.value))||Number(n.params.value)>255))errors.push(`${n.id}: PWM duty must be 0..255`);
    if(n.type==='serialPrint'&&(typeof n.params.text!=='string'||n.params.text.length>160||![9600,19200,38400,57600,115200].includes(Number(n.params.baud))))errors.push(`${n.id}: serial message <=160 chars; baud must be 9600/19200/38400/57600/115200`);
  }
  if(new Set(ordered.filter(n=>n.type==='serialPrint').map(n=>String(n.params.baud))).size>1)errors.push('Serial nodes have conflicting baud rates');
  const pin=pinDiagnostics(p); errors.push(...pin.errors); warnings.push(...pin.warnings);
  return {ok:errors.length===0, errors, warnings, ordered};
}
function generateSketch(p) {
  verifyProject(p);
  if(p.source.mode==='manual') return {source:p.source.manualSource, diagnostics:{ok:true,errors:[],warnings:['Manual mode: graphical blocks do not affect this source'],ordered:[]}};
  const isFlow=p.visualMode==='flowchart';
  const diagnostics=isFlow?flow.validateFlowchart(p.flowchart||flow.sampleFlowchart(),{boardPins:PIN_PROFILES[p.fqbn],boardFqbn:p.fqbn}):analyzeGraph(p);
  if(isFlow && p.peripherals?.length){const resourcePlan=peripherals.plan(p);diagnostics.errors.push(...resourcePlan.errors);diagnostics.warnings.push(...resourcePlan.warnings);diagnostics.ok=diagnostics.errors.length===0;}
  if(!diagnostics.ok) return {source:null,diagnostics};
  const setup=[],loop=[];let needsWire=false,serialBaud=null;
  function addGraph(targetSetup,targetLoop) {
    const graph=analyzeGraph(p);if(!graph.ok)return graph;
    for(const n of graph.ordered){const pin=Number(n.params.pin);
      switch(n.type){case 'pinMode':targetSetup.push(`  pinMode(${pin}, ${n.params.mode}); // node:${n.id}`);break;
      case 'digitalWrite':targetLoop.push(`  digitalWrite(${pin}, ${n.params.value}); // node:${n.id}`);break;
      case 'delay':targetLoop.push(`  delay(${Number(n.params.ms)}UL); // node:${n.id}`);break;
      case 'pwmWrite':targetSetup.push(`  pinMode(${pin}, OUTPUT); // node:${n.id} PWM`);targetLoop.push(`  analogWrite(${pin}, ${Number(n.params.value)}); // node:${n.id}`);break;
      case 'serialPrint':serialBaud=Number(n.params.baud);targetLoop.push(`  Serial.println(${JSON.stringify(n.params.text)}); // node:${n.id}`);break;
      case 'wireWrite':needsWire=true;targetLoop.push(...wire.emit(n));break;
      case 'comment':targetLoop.push(`  // ${String(n.params.text||'').replace(/[\r\n]/g,' ').replace(/\*\//g,'')} // node:${n.id}`);break;}
    }return graph;
  }
  let graphFunction='';
  if(isFlow){const generated=flow.flowchartSource(p.flowchart||flow.sampleFlowchart());setup.push(...generated.setup);loop.push(...generated.loop);
    if(generated.needsNodeCall){const extraSetup=[],extraLoop=[];const g=addGraph(extraSetup,extraLoop);if(!g.ok)return {source:null,diagnostics:g};setup.push(...extraSetup);graphFunction=`void blazeNodesTick() {\n${extraLoop.join('\n')}\n}\n\n`;}
  }else addGraph(setup,loop);
  if(needsWire)setup.unshift('  Wire.begin(); // curated core library');
  if(serialBaud!==null)setup.unshift(`  Serial.begin(${serialBaud});`);
  return {source:`// Blaze MCU Studio v0.4.2 - ${p.name.replace(/[\r\n]/g,' ')}\n// Generated visual regions are rebuilt; user regions are preserved.\n${needsWire?'#include <Wire.h>\nuint8_t blazeLastWireStatus = 0;\n':''}${p.source.userPrelude}\n\n${graphFunction}void setup() {\n${setup.join('\n')}\n// BEGIN USER SETUP\n${p.source.userSetup}\n// END USER SETUP\n}\n\nvoid loop() {\n${loop.join('\n')}\n// BEGIN USER LOOP\n${p.source.userLoop}\n// END USER LOOP\n}\n`,diagnostics,dependencies:needsWire?['Wire']:[]};
}
module.exports={SCHEMA_VERSION, FQBN_RE, NAME_RE, createProject, verifyProject, analyzeGraph, generateSketch, pinDiagnostics, sketchName, PIN_PROFILES};
