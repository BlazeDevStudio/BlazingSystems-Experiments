'use strict';
const {test}=require('node:test');const assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {createProject,generateSketch}=require('../core/project.cjs');
const {WorkspaceStore}=require('../core/storage.cjs');
const {SimulationController}=require('../core/simulator.cjs');
const {asByte}=require('../core/curated-adapters.cjs');
function add(p,type,params){let previous=p.graph.edges.at(-1)[1],id=type+'_'+p.graph.nodes.length;p.graph.nodes.push({id,type,params,x:600,y:500});p.graph.edges.push([previous,id]);return p;}
test('Uno Wire register-write emits correct library initialization, transaction and dependency',()=>{
 const p=add(createProject('WireUno'),'wireWrite',{address:'0x3C',register:'0x01',value:'255'}),r=generateSketch(p);
 assert.equal(r.diagnostics.ok,true,r.diagnostics.errors.join('; '));assert.deepEqual(r.dependencies,['Wire']);
 for(const token of ['#include <Wire.h>','Wire.begin();','Wire.beginTransmission((uint8_t)60)','Wire.write((uint8_t)1)','Wire.write((uint8_t)255)','blazeLastWireStatus = Wire.endTransmission()'])assert(r.source.includes(token),token);
 assert.equal((r.source.match(/Wire.begin\(\)/g)||[]).length,1);
});
test('Unverified ESP core rejects automatic Wire C++ adapter without changing user sketch',()=>{
 const p=add(createProject('WireEsp','esp8266:esp8266:generic'),'wireWrite',{address:'60',register:'0',value:'1'});
 assert.equal(generateSketch(p).source,null);assert.match(generateSketch(p).diagnostics.errors.join(' '),/only compile-gated on Arduino Uno/);
 p.source.mode='manual';p.source.manualSource='void setup() {}\nvoid loop() {}';assert.equal(generateSketch(p).source,p.source.manualSource);
});
test('Wire payloads reject injected C++ and reserved I2C addresses',()=>{
 for(const bad of ['12; system(1)','0xZZ','119.5','-1','256']) assert.throws(()=>asByte(bad,'test'),/test:/);
 for(const address of ['0x00','7','120','127']){const p=add(createProject('Blocked'),'wireWrite',{address,register:'0',value:'1'});assert.equal(generateSketch(p).source,null);}
});
test('The export identifies a used Wire dependency but does not overwrite target files',()=>{
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'blaze-wire-'));
 try{const p=add(createProject('WireExport'),'wireWrite',{address:'60',register:'0',value:'1'});const store=new WorkspaceStore(path.join(root,'store'));const exported=store.export(p,path.join(root,'out'));
 const m=JSON.parse(fs.readFileSync(path.join(exported.folder,'blaze-project.json')));
 assert(m.libraryDependencies.includes('Wire'));
 assert.throws(()=>store.export(p,path.join(root,'out')),/refused/);
 }finally{fs.rmSync(root,{recursive:true,force:true});}
});
test('PWM validation checks Uno physical PWM pins and duty limits',()=>{
 for(const pin of ['2','4','12']){const p=add(createProject('PwmPin'),'pwmWrite',{pin,value:'128'});assert.equal(generateSketch(p).source,null);}
 for(const value of ['256','-1','abc','4.3']){const p=add(createProject('PwmDuty'),'pwmWrite',{pin:'9',value});assert.equal(generateSketch(p).source,null);}
 const p=add(createProject('PwmValid'),'pwmWrite',{pin:'9',value:'128'});assert.match(generateSketch(p).source,/analogWrite\(9, 128\)/);
});
test('Serial messages escape C++ literal and mixed baud rates cannot compile',()=>{
 const p=add(createProject('SerialLog'),'serialPrint',{text:'hello "world"\\',baud:'9600'});let r=generateSketch(p);assert(r.diagnostics.ok);assert.match(r.source,/Serial.begin\(9600\)/);assert.match(r.source,/Serial.println\("hello \\"world\\"\\\\"\)/);
 add(p,'serialPrint',{text:'next',baud:'115200'});r=generateSketch(p);assert.equal(r.source,null);assert.match(r.diagnostics.errors.join(' '),/conflicting baud/);
});
test('Logic simulator distinguishes PWM preview from unmodeled physical I2C',()=>{
 const p=add(add(createProject('VirtualPeripheral'),'pwmWrite',{pin:'9',value:'128'}),'wireWrite',{address:'60',register:'0',value:'1'});
 const simulator=new SimulationController();const created=simulator.create(p);const report=simulator.run(created.id,{maxSteps:100});
 assert.equal(report.pwm['9'],128);assert.match(report.warnings.join(' '),/hardware model/);assert(report.events.some(e=>e.type==='wireWrite'&&/NOT emulated/.test(e.effect)));
});
test('Flowchart calls into the same Wire-enabled graph without losing setup or ownership',()=>{
 const {step}=require('../core/flowchart.cjs');
 const p=add(createProject('ComposedWire'),'wireWrite',{address:'60',register:'0',value:'1'});
 p.visualMode='flowchart';p.flowchart.steps=[step('call','callNodes')];
 const r=generateSketch(p);assert.equal(r.diagnostics.ok,true,r.diagnostics.errors.join('; '));
 assert.equal((r.source.match(/Wire.begin\(\)/g)||[]).length,1);
 assert.match(r.source,/void blazeNodesTick\(\)/);assert.match(r.source,/blazeLastWireStatus = Wire.endTransmission/);
 assert.match(r.source,/blazeNodesTick\(\);/);
 p.source.userSetup='// preserved user configuration';
 assert.match(generateSketch(p).source,/preserved user configuration/);
});
