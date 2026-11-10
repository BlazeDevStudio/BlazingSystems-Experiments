#!/usr/bin/env node
'use strict';
const path=require('node:path');
const {createProject,generateSketch}=require('../core/project.cjs');
const {WorkspaceStore}=require('../core/storage.cjs');
const dest=process.argv[2];if(!dest){console.error('Output folder required');process.exit(2);}
const p=createProject('GeneratedWirePWMSerial','arduino:avr:uno');
for(const [i,[type,params]] of [
 ['pwmWrite',{pin:'9',value:'128'}],
 ['wireWrite',{address:'0x3C',register:'0x02',value:'0x7F'}],
 ['serialPrint',{text:'wire status follows',baud:'9600'}]
].entries()){
 const id='extension'+i,previous=p.graph.edges.at(-1)[1];
 p.graph.nodes.push({id,type,params,x:200,y:500+i*100});p.graph.edges.push([previous,id]);
}
const generated=generateSketch(p);
if(!generated.diagnostics.ok||!generated.dependencies?.includes('Wire'))throw Error('Curated adapter failed verification: '+generated.diagnostics.errors.join('; '));
const r=new WorkspaceStore(path.join(dest,'.extended-project-store')).export(p,dest);
console.log('Generated Uno Wire/PWM/Serial firmware: '+r.filename);
