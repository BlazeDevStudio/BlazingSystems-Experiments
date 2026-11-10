'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {WorkspaceStore}=require('../core/storage.cjs'),{WorkspaceCatalog}=require('../core/workspaces.cjs');
function fixture(fn){const root=fs.mkdtempSync(path.join(os.tmpdir(),'blaze-ws-'));try{return fn(new WorkspaceStore(root),root);}finally{fs.rmSync(root,{recursive:true,force:true});}}
test('a workspace groups independent Uno and ESP projects, persisted across catalog reload',()=>fixture((ps,root)=>{
 const uno=ps.create('Motor','arduino:avr:uno'),esp=ps.create('Gateway','esp32:esp32:esp32');
 const cat=new WorkspaceCatalog(ps),w=cat.create('Home Automation');cat.add(w.id,uno.id);cat.add(w.id,esp.id);
 const reopened=new WorkspaceCatalog(new WorkspaceStore(root)).get(w.id);
 assert.deepEqual(reopened.projectIds,[uno.id,esp.id]);assert.deepEqual(reopened.missingIds,[]);
 assert.equal(ps.open(uno.id).fqbn,'arduino:avr:uno');assert.equal(ps.open(esp.id).fqbn,'esp32:esp32:esp32');
 cat.add(w.id,uno.id);assert.equal(cat.get(w.id).projectIds.length,2);
}));
test('workspace rename, unlink, deletion never modifies or deletes member firmware',()=>fixture(ps=>{
 const a=ps.create('Uno'),cat=new WorkspaceCatalog(ps),w=cat.create('Lab');cat.add(w.id,a.id);cat.rename(w.id,'Lab A');assert.equal(cat.get(w.id).name,'Lab A');
 cat.remove(w.id,a.id);assert.deepEqual(cat.get(w.id).projectIds,[]);cat.add(w.id,a.id);
 assert.deepEqual(cat.delete(w.id),{id:w.id,removedAssociationCount:1,projectsDeleted:0});assert.equal(ps.open(a.id).name,'Uno');assert.equal(cat.list().length,0);
}));
test('recoverable deleted project stays referenced and visibly missing, then recovered',()=>fixture(ps=>{
 const p=ps.create('Retained'),cat=new WorkspaceCatalog(ps),w=cat.create('Research');cat.add(w.id,p.id);ps.trash(p.id);
 assert.deepEqual(cat.get(w.id).missingIds,[p.id]);assert.equal(cat.get(w.id).projectIds.length,1);
 assert.throws(()=>cat.add(w.id,p.id));ps.recover(p.id);assert.deepEqual(cat.get(w.id).missingIds,[]);
}));
test('invalid and nonexisting members rejected, no path traversal, no silent catalog changes',()=>fixture((ps,root)=>{
 const c=new WorkspaceCatalog(ps),w=c.create('Valid');for(const bad of ['','../../x','\n','    ']){
  if(bad==='../../x')continue;
  assert.throws(()=>c.create(bad));
 }
 assert.throws(()=>c.add(w.id,'../../unsafe'),/Invalid project ID/);
 assert.throws(()=>c.add(w.id,'11111111-1111-4111-8111-111111111111'));
 assert.throws(()=>c.rename(w.id,'a\u0000b'));
 assert.deepEqual(c.get(w.id).projectIds,[]);
 const invalidPath=path.join(root,'_workspaces.json');fs.writeFileSync(invalidPath,'{"version":1,"items":[{"id":"../../tmp","name":"Unsafe","projectIds":[]}]}' );
 assert.throws(()=>c.list(),/Invalid workspace catalog/);
}));
test('corrupt workspace metadata fails closed without affecting independent project access',()=>fixture((ps,root)=>{
 const p=ps.create('Sketch');fs.writeFileSync(path.join(root,'_workspaces.json'),'{not-json');
 const cat=new WorkspaceCatalog(ps);assert.throws(()=>cat.create('Another'));assert.equal(ps.open(p.id).name,'Sketch');
}));
