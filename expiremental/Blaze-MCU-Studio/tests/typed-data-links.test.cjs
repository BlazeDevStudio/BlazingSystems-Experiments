'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {createProject,generateSketch,analyzeGraph,verifyProject}=require('../core/project.cjs');
const {SimulationController}=require('../core/simulator.cjs');
const {WorkspaceStore}=require('../core/storage.cjs');
const {plan}=require('../core/data-links.cjs');
function connected(){
 const p=createProject('DataPipe','arduino:avr:uno','sensor-threshold');
 p.variables.push({name:'command',type:'long',initial:'0'});
 const setter={id:'assignCommand',type:'setVariable',params:{target:'command',value:'200'},x:480,y:320};
 p.graph.nodes.push(setter);
 p.graph.edges=[['start','analogSample'],['analogSample','assignCommand'],['assignCommand','threshold']];
 p.graph.dataEdges=[{from:'assignCommand',to:'threshold',out:'value',input:'measurement'}];
 return p;
}
test('data edge changes real firmware source from nominal inspector variable to wired numeric value',()=>{
 const p=connected();assert.equal(p.graph.nodes.find(n=>n.id==='threshold').params.variable,'sensorValue');
 const g=generateSketch(p);assert(g.diagnostics.ok,g.diagnostics.errors.join('; '));
 assert.match(g.source,/blazeVar_command >= 512L/);assert.doesNotMatch(g.source,/blazeVar_sensorValue >= 512L/);
 assert.match(g.source,/blazeVar_command = 200L/);
 const s=new SimulationController(),session=s.create(p);s.analog(session.id,{A0:700});const outcome=s.run(session.id,{maxSteps:100});
 assert.equal(outcome.variables.sensorValue,700);assert.equal(outcome.variables.command,200);assert.equal(outcome.outputs['8'],'LOW');
});
test('removing data edge restores explicitly selected inspector variable',()=>{
 const p=connected();p.graph.dataEdges=[];const g=generateSketch(p);assert(g.diagnostics.ok);assert.match(g.source,/blazeVar_sensorValue >= 512L/);
 const sim=new SimulationController(),instance=sim.create(p);sim.analog(instance.id,{A0:700});assert.equal(sim.run(instance.id,{maxSteps:100}).outputs['8'],'HIGH');
});
test('bool source rejected as incompatible numeric measurement, no source emitted',()=>{
 const p=connected();p.variables.push({name:'on',type:'bool',initial:'true'});
 const source=p.graph.nodes.find(n=>n.id==='assignCommand');source.params.target='on';source.params.value='true';
 const g=generateSketch(p);assert.equal(g.source,null);assert.match(g.diagnostics.errors.join(' '),/bool output is incompatible/);
 assert.throws(()=>new SimulationController().create(p),/Resolve source validation/);
});
test('producer must precede consumer in actual execution path',()=>{
 const p=connected();p.graph.edges=[['start','analogSample'],['analogSample','threshold'],['threshold','assignCommand']];
 const g=generateSketch(p);assert.equal(g.source,null);assert.match(g.diagnostics.errors.join(' '),/must execute before consumer/);
});
test('one consumer cannot accept multiple numeric data drivers',()=>{
 const p=connected();p.graph.dataEdges.push({from:'analogSample',to:'threshold',out:'value',input:'measurement'});
 assert.equal(generateSketch(p).source,null);assert.match(analyzeGraph(p).errors.join(' '),/multiple wires/);
});
test('missing node, unsupported sockets and malformed data edges fail closed',()=>{
 for(const other of [
  {from:'missing',to:'threshold',out:'value',input:'measurement'},
  {from:'assignCommand',to:'threshold',out:'object',input:'measurement'},
  {from:'threshold',to:'assignCommand',out:'value',input:'measurement'}
 ]){const p=connected();p.graph.dataEdges=[other];assert.equal(generateSketch(p).source,null);}
 const p=connected();p.graph.dataEdges=[{from:'assignCommand',to:'threshold',out:'value',input:'measurement',script:'rm -rf'}];
 assert.throws(()=>verifyProject(p),/Malformed typed data connection/);
});
test('data-edge project survives disk save, export and manual C++ ownership',()=>{
 const p=connected(),root=fs.mkdtempSync(path.join(os.tmpdir(),'blaze-data-links-'));
 try{
  const store=new WorkspaceStore(path.join(root,'projects'));store.save(p);const reopened=store.open(p.id);
  assert.deepEqual(reopened.graph.dataEdges,p.graph.dataEdges);
  const exported=store.export(reopened,path.join(root,'sketches'));
  assert.match(fs.readFileSync(exported.filename,'utf8'),/blazeVar_command >= 512L/);
  reopened.source.mode='manual';reopened.source.manualSource='void setup() {}\nvoid loop() {}';
  assert.equal(generateSketch(reopened).source,reopened.source.manualSource);
 }finally{fs.rmSync(root,{recursive:true,force:true});}
});
test('legacy projects without dataEdges still compile and simulate',()=>{
 const p=createProject('Old','arduino:avr:uno','sensor-threshold');delete p.graph.dataEdges;
 assert.equal(plan(p,analyzeGraph(p).ordered).ok,true);assert.match(generateSketch(p).source,/blazeVar_sensorValue >= 512L/);
});

test('typed connection GUI calls a real exposed preload validation method',()=>{
 const root=path.join(__dirname,'..');
 const preload=fs.readFileSync(path.join(root,'electron/preload.cjs'),'utf8');
 const renderer=fs.readFileSync(path.join(root,'renderer/app.js'),'utf8');
 assert.match(preload,/validate:'project:validate'/);
 assert.match(renderer,/window\.blaze\.validate\(structuredClone\(project\)\)/);
 assert.doesNotMatch(renderer,/window\.blaze\.validateProject\(/);
});
