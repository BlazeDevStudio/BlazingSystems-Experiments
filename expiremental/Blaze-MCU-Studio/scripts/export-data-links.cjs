#!/usr/bin/env node
'use strict';
const path=require('node:path');
const {createProject,generateSketch}=require('../core/project.cjs');
const {WorkspaceStore}=require('../core/storage.cjs');
const root=process.argv[2];if(!root)throw Error('Output directory required');
const p=createProject('GeneratedTypedDataWire','arduino:avr:uno','sensor-threshold');
p.variables.push({name:'command',type:'long',initial:'0'});
p.graph.nodes.push({id:'commandSource',type:'setVariable',params:{target:'command',value:'700'},x:500,y:290});
p.graph.edges=[['start','analogSample'],['analogSample','commandSource'],['commandSource','threshold']];
p.graph.dataEdges=[{from:'commandSource',to:'threshold',out:'value',input:'measurement'}];
const built=generateSketch(p);
if(!built.diagnostics.ok||!built.source.includes('blazeVar_command >= 512L'))throw Error('Typed data connection did not generate expected executable C++');
const result=new WorkspaceStore(path.join(root,'.typed-data-store')).export(p,root);
console.log('Generated typed linked Arduino Uno sketch: '+result.filename);
