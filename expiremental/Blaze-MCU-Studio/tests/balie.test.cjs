'use strict';const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const balie=require('../core/balie.cjs'),{createProject}=require('../core/project.cjs'),board=require('../core/board.cjs');
function fixture(fn){const d=fs.mkdtempSync(path.join(os.tmpdir(),'blaze-balie-'));try{const root=path.join(d,'libraries','TemperatureLab');fs.mkdirSync(path.join(root,'src'),{recursive:true});fs.writeFileSync(path.join(root,'library.properties'),'name=TemperatureLab\nversion=0.4.3\narchitectures=avr,esp32\nlicense=MIT\n');fs.writeFileSync(path.join(root,'src','TemperatureLab.h'),'float readTemperature();\nbool beginSensor(int pin);\n');return fn(d,root);}finally{fs.rmSync(d,{recursive:true,force:true});}}
test('BALIE parses metadata and C-style API signatures without execution',()=>fixture((d,root)=>{const r=balie.inspectLibrary(root,'avr');assert.equal(r.name,'TemperatureLab');assert.equal(r.boardCompatible,true);assert(r.api.some(f=>f.name==='readTemperature'));assert.equal(r.analysis,'inferred');assert.equal(r.verifiedForBoard,false);assert.equal(balie.libraryNodes(r)[0].codegen,'manual-adapter-required');}));
test('architecture incompatibility remains visible',()=>fixture((d,root)=>{const r=balie.inspectLibrary(root,'samd');assert.equal(r.boardCompatible,false);}));
test('library changes invalidate content hash',()=>fixture((d,root)=>{const old=balie.inspectLibrary(root);fs.appendFileSync(path.join(root,'src','TemperatureLab.h'),'int getHumidity();\n');const next=balie.inspectLibrary(root);assert.notEqual(next.sourceHash,old.sourceHash);}));
test('sketchbook library scanning indexes only directories with metadata',()=>fixture((d,root)=>{const r=balie.scanInstalled({sketchbook:d,architecture:'avr'});assert.equal(r.libraries.length,1);}));
test('overlarge untrusted header rejected but library metadata retained',()=>fixture((d,root)=>{fs.writeFileSync(path.join(root,'src','TemperatureLab.h'),'x'.repeat(600000));const r=balie.inspectLibrary(root);assert.match(r.warnings.join(' '),/too large/);}));
test('board migration never asserts unknown pin capability',()=>{const p=createProject('Board','arduino:avr:uno');const report=board.analyzeBoardChange(p,'esp32:esp32:esp32');assert.equal(report.compatible,false);assert.match(report.warnings.join(' '),/not verified/);});
test('core-provided libraries discovered under Arduino15 installed platform roots',()=>{
 const {platformLibraryRoots,scanInstalled}=require('../core/balie.cjs');
 const base=fs.mkdtempSync(path.join(os.tmpdir(),'blaze-core-libs-'));
 try{
  const library=path.join(base,'packages','esp8266','hardware','esp8266','3.1.2','libraries','Wire');
  fs.mkdirSync(library,{recursive:true});fs.writeFileSync(path.join(library,'library.properties'),'name=Wire\nversion=1.0.0\narchitectures=esp8266\n');
  fs.writeFileSync(path.join(library,'Wire.h'),'float readTemp();');
  const roots=platformLibraryRoots(base);assert.equal(roots.length,1);
  const found=scanInstalled({sketchbook:path.join(base,'nonexistent'),architecture:'esp8266',dataDirectory:base});
  assert(found.libraries.some(x=>x.name==='Wire'&&x.api.some(y=>y.name==='readTemp')));
 }finally{fs.rmSync(base,{recursive:true,force:true});}
});
