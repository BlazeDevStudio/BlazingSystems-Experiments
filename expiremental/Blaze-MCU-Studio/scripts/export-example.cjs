#!/usr/bin/env node
'use strict';
// Generate the same source that the UI compiles/exports from the project IR.
const {createProject}=require('../core/project.cjs');
const {WorkspaceStore}=require('../core/storage.cjs');
const path=require('node:path');
const dest=process.argv[2];
if(!dest){console.error('Usage: node scripts/export-example.cjs <existing empty parent folder>');process.exit(2);}
const project=createProject('GeneratedBlink','arduino:avr:uno');
const result=new WorkspaceStore(path.join(dest,'.blaze-test-store')).export(project,dest);
console.log('Generated source: '+result.filename);
