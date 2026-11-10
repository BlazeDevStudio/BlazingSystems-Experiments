'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const {createProject,generateSketch}=require('../core/project.cjs');
const {step}=require('../core/flowchart.cjs');
test('node source map resolves to exact generator lines without modifying emitted Arduino source',()=>{
 const p=createProject('CodeTour'),g=generateSketch(p);assert(g.diagnostics.ok);assert(g.source.includes('digitalWrite(13, HIGH)'));
 for(const e of g.sourceMap){assert.equal(g.source.split('\n')[e.line-1].trim(),e.code);assert(e.line>0);}
 assert(g.sourceMap.some(x=>x.id==='mode'&&x.section==='setup'));
 assert(g.sourceMap.some(x=>x.id==='on'&&x.section==='loop'&&x.code.includes('HIGH')));
 assert(g.sourceMap.some(x=>x.id==='wait1'&&x.code.includes('1000')));
});
test('source map must ignore user-owned source even with forged visual marker',()=>{
 const p=createProject('Untrusted');p.source.userPrelude='// node:on\n// flow:pinsetup';p.source.userSetup='  digitalWrite(13, HIGH); // node:on';p.source.userLoop='// node:on\n// flow:on';
 const g=generateSketch(p),matches=g.sourceMap.filter(x=>x.id==='on');assert.equal(matches.length,1);assert(matches[0].code.startsWith('digitalWrite(13, HIGH)'));
 assert(!g.sourceMap.some(x=>x.code==="// node:on"));
});
test('manual source is never reverse-mapped to the visual graph',()=>{
 const p=createProject('Manual');p.source.mode='manual';p.source.manualSource='// node:on\nvoid setup(){}\nvoid loop(){}';
 assert.deepEqual(generateSketch(p).sourceMap||[],[]);
});
test('flowchart source map attributes nested decisions and output statements',()=>{
 const p=createProject('FlowTour');p.visualMode='flowchart';p.flowchart.steps=[step('cond','branch',{pin:'2',equals:'HIGH'},[step('led','write',{pin:'13',value:'HIGH'})],[])];
 const g=generateSketch(p);assert(g.diagnostics.ok,g.diagnostics.errors.join(','));
 assert(g.sourceMap.some(x=>x.kind==='flow'&&x.id==='cond'&&x.code.startsWith('if (digitalRead')));
 assert(g.sourceMap.some(x=>x.kind==='flow'&&x.id==='led'&&x.code.includes('digitalWrite')));
});
test('flowchart explicit node invocation maps both generated node function and flow step',()=>{
 const p=createProject('CombinedTour');p.visualMode='flowchart';p.flowchart.steps=[step('execute','callNodes')];
 const g=generateSketch(p);assert(g.diagnostics.ok,g.diagnostics.errors.join(','));
 assert(g.sourceMap.some(x=>x.section==='nodes'&&x.id==='on'));
 assert(g.sourceMap.some(x=>x.kind==='flow'&&x.id==='execute'));
});
test('custom generated comments never masquerade as source-map entries for deleted nodes',()=>{
 const p=createProject('CommentTour');p.graph.nodes.find(x=>x.id==='wait1').params.ms=95;
 const g=generateSketch(p);assert(g.sourceMap.find(x=>x.id==='wait1').code.includes('95UL'));
 assert(!g.sourceMap.some(x=>x.id==='nonexistent'));
});

test('user source may contain forged section markers without breaking generation or mapping',()=>{
 const p=createProject('ForgedLabels');
 p.source.userPrelude='// BEGIN USER SETUP\nvoid setup() {\n// BEGIN USER LOOP';
 p.source.userSetup='// BEGIN USER SETUP\n// node:on';
 p.source.userLoop='// BEGIN USER LOOP\n// node:on\nvoid loop() {';
 const g=generateSketch(p);
 assert.equal(g.sourceMap.filter(e=>e.id==='on').length,1);
 assert(g.sourceMap.some(e=>e.kind==='node'&&e.id==='mode'));
});
