#!/usr/bin/env node
'use strict';
const path=require('node:path');const {createProject,generateSketch}=require('../core/project.cjs');const {WorkspaceStore}=require('../core/storage.cjs');
const dest=process.argv[2];if(!dest)throw Error('Destination folder required');
const p=createProject('GeneratedSensorThreshold','arduino:avr:uno');p.variables=[{name:'sensorValue',type:'long',initial:'0'}];
for(const [type,params] of [['readAnalog',{pin:'A0',target:'sensorValue'}],['thresholdOutput',{pin:'8',variable:'sensorValue',operator:'>=',threshold:'512',trueValue:'HIGH',falseValue:'LOW'}]]){
 const prev=p.graph.edges.at(-1)[1],id='sensor'+p.graph.nodes.length;p.graph.nodes.push({id,type,params,x:500,y:500});p.graph.edges.push([prev,id]);
}
const output=new WorkspaceStore(path.join(dest,'.sensor-test-store')).export(p,dest);if(!generateSketch(p).diagnostics.ok)throw Error('Sensor threshold generation invalid');console.log('Generated sensor threshold firmware: '+output.filename);
