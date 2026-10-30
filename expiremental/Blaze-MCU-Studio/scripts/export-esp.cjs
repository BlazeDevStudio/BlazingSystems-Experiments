#!/usr/bin/env node
'use strict';
const path=require('node:path');
const {createProject,generateSketch}=require('../core/project.cjs');
const {WorkspaceStore}=require('../core/storage.cjs');
const root=process.argv[2];if(!root)throw Error('Expected destination root');
for(const [fqbn,name,pin] of [
 ['esp8266:esp8266:generic','BlazeESP8266Blink','4'],
 ['esp32:esp32:esp32','BlazeESP32Blink','21']]){
 const p=createProject(name,fqbn,'blink');const out=generateSketch(p);
 if(!out.source||!out.diagnostics.ok||!out.source.includes(`pinMode(${pin}, OUTPUT)`))throw Error(`Invalid ${fqbn} generated firmware`);
 const result=new WorkspaceStore(path.join(root,'.temporary-store-'+name)).export(p,root);
 console.log(JSON.stringify({fqbn,name,pin,sketch:result.filename,sourceBytes:Buffer.byteLength(out.source)}));
}
