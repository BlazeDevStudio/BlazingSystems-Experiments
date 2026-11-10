#!/usr/bin/env node
'use strict';
const {createProject}=require('../core/project.cjs'),{step}=require('../core/flowchart.cjs');const {WorkspaceStore}=require('../core/storage.cjs');const path=require('node:path');
const dest=process.argv[2];if(!dest){console.error('Destination directory required');process.exit(2);}
const p=createProject('GeneratedFlowchart','arduino:avr:uno');p.visualMode='flowchart';p.flowchart.steps=[step('setup','setOutput',{pin:'13'}),step('decision','branch',{pin:'2',equals:'HIGH'},[step('retry','repeat',{count:3},[step('on','write',{pin:'13',value:'HIGH'}),step('wait','wait',{ms:30})])],[step('off','write',{pin:'13',value:'LOW'})])];
const output=new WorkspaceStore(path.join(dest,'.flowchart-test-store')).export(p,dest);console.log('Generated flowchart firmware: '+output.filename);
