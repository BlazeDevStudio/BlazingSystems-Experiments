#!/usr/bin/env node
'use strict';
const path=require('node:path'),{createProject,generateSketch}=require('../core/project.cjs'),{WorkspaceStore}=require('../core/storage.cjs');
const dest=process.argv[2];if(!dest)throw Error('Output folder required');
for(const [name,fqbn] of [['GeneratedMegaBlink','arduino:avr:mega'],['GeneratedNanoBlink','arduino:avr:nano']]){
 const p=createProject(name,fqbn);const r=generateSketch(p);if(!r.diagnostics.ok)throw Error(fqbn+': '+r.diagnostics.errors.join('; '));
 const exported=new WorkspaceStore(path.join(dest,'.target-smoke-store')).export(p,dest);console.log(name,fqbn,exported.filename,'pinout evidence: '+r.diagnostics.warnings.join('; '));
}
